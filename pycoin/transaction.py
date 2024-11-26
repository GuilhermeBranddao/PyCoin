import datetime
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey

from pycoin.exceptions.transaction_exceptions import TransactionError
from pycoin.settings.config import Settings
from pycoin.wallet import Wallet

settings = Settings()
# Tamanho truncado do endereço em bytes
ADDRESS_LENGTH = 16  # 16 bytes (128 bits)
CHECKSUM_LENGTH = 4  # Checksum de 4 bytes


class Transaction:
    def __init__(self):
        """
        Inicializa uma nova transação.

        :param private_key_sender chave do sender
        :param public_key_sender chave do sender
        :param recipient: O endereço do destinatário.
        :param amount: O valor a ser transferido.
        """

        self.transactions_file_path = settings.TRANSACTIONS_FILE

    def sign_transaction(self, public_key: str, private_key: str,
                         recipient_address: str, amount: float):
        """
        Assina a transação usando a chave privada do remetente.

        :param private_key: A chave privada do remetente.
        :param public_key_sender: A chave pública correspondente.
        """

        # Converte
        private_key = Wallet.load_private_key_from_string(key_string=private_key)
        public_key = Wallet.load_public_key_from_string(key_string=public_key)

        self.address_sender = Wallet.generate_address(public_key=public_key)

        if not Wallet.validate_key_pair(private_key=private_key,
                                      public_key=public_key):
            raise ValueError('Chave privada e chave pública não correspondem.')

        if self.address_sender == recipient_address:
            raise ValueError('O remetente e o destinatário não podem ser iguais.')

        if not Wallet.is_validate_address(recipient_address):
            raise ValueError('O endereço do destinatário é invalido.')

        transaction_data = self._get_transaction_data(
            self.address_sender, recipient_address, amount
        )
        self.signature = private_key.sign(
            transaction_data, ec.ECDSA(hashes.SHA256())
        )

        if self.verify_signature(public_key, recipient_address, amount):
            return True
        else:
            raise ValueError('Transação inválida! A assinatura não corresponde.')

    def verify_signature(self, public_key: EllipticCurvePrivateKey,
                         recipient_address: str, amount: float):
        """
        Verifica a assinatura da transação usando a chave pública do remetente.

        :param public_key: A chave pública do remetente.
        :return: True se a assinatura for válida, False caso contrário.
        """

        address_sender = Wallet.generate_address(public_key=public_key)

        transaction_data = self._get_transaction_data(
            address_sender, recipient_address, amount
        )

        try:
            public_key.verify(
                self.signature, transaction_data, ec.ECDSA(hashes.SHA256())
            )
            return True
        except InvalidSignature:
            return False

    @staticmethod
    def _get_transaction_data(address_sender, recipient_address, amount):
        """
        Concatena os dados da transação (address_sender, recipient, amount) em bytes

        com delimitadores.
        :return: Dados da transação em formato binário.
        """
        transaction_data = f'{address_sender}|{recipient_address}|{amount}'
        return transaction_data.encode('utf-8')

    @staticmethod
    def _decode_transaction_data(transaction_data):
        """
        Decodifica os dados da transação de volta para address_sender, recipient e amount.
        :param transaction_data: Dados binários da transação.
        :return: Um dicionário com as informações da transação.
        """
        decoded_data = transaction_data.decode('utf-8')
        address_sender, recipient_address, amount = decoded_data.split('|')

        return {
            'address_sender': address_sender,
            'recipient_address': recipient_address,
            'amount': float(amount),
        }

    @staticmethod
    def save_transactions(transactions_file_path: Path, transaction_data: list) -> bool:
        """
        Salva as transações do arquivo JSON, mantendo a estrutura básica.
        """
        print('Salvando transações')

        if not isinstance(transactions_file_path, Path):
            raise ValueError("O parâmetro transactions_file_path deve ser um objeto do tipo Path.")

        existing_transaction = Transaction.load_transactions(transactions_file_path)
        new_transaction = transaction_data + existing_transaction

        # Adiciona a nova transação ao conjunto de transações existentes
        transactions = {"transactions": new_transaction}

        # Salva as transações atualizadas de volta ao arquivo
        with open(transactions_file_path, 'w', encoding='utf-8') as file:
            json.dump(transactions, file, indent=4)

        return True

    @staticmethod
    def load_transactions(transactions_file_path: Path = settings.TRANSACTIONS_FILE) -> list:
        """
        Carrega todas as transações do arquivo JSON, mantendo a estrutura básica.
        """
        print("Carregando transações")
        if not isinstance(transactions_file_path, Path):
            raise ValueError("O parâmetro block_file_path deve ser um objeto do tipo Path.")

        if not transactions_file_path.exists():
            transactions_file_path.parent.mkdir(parents=True, exist_ok=True)
            transactions_file_path.touch()

        if transactions_file_path.exists():
            try:
                with open(transactions_file_path, 'r', encoding='utf-8') as file:
                    transaction = json.load(file)
                    return transaction['transactions']
            except json.JSONDecodeError:
                print("Erro ao carregar o arquivo. Retornando lista vazia.")
                return []
            except Exception as e:
                print(f"Error: {e}")

    @staticmethod
    def clear_transactions(transactions_file_path: str) -> bool:
        """
        Remove todas as transações do arquivo JSON.
        """
        print('Limpando transações')

        # Define a estrutura vazia padrão
        empty_transactions = {"transactions": []}

        # Sobrescreve o arquivo com a estrutura vazia
        with open(transactions_file_path, 'w', encoding='utf-8') as file:
            json.dump(empty_transactions, file, indent=4)

        print(f"Todas as transações foram removidas de {transactions_file_path}.")
        return True

    @staticmethod
    def add_transaction_miner_reward(miner_address: str,
                                     reward_amount: float,
                                     message_address: str = "MINING_REWARD"):
        """
        Adiciona uma transação de recompensa para o minerador.
        """
        if reward_amount <= 0:
            raise TransactionError('A recompensa deve ser maior que zero.', status_code=422)

        # Cria a transação de recompensa
        transaction_data = [{
            'address_sender': message_address,  # Indicador especial para transações de recompensa
            'recipient_address': miner_address,
            'amount': float(reward_amount),
            'timestamp': str(datetime.datetime.now()),
        }]

        # Salva a transação diretamente
        Transaction.save_transactions(transactions_file_path=settings.TRANSACTIONS_FILE,
                                      transaction_data=transaction_data)

        return True

    def add_transaction(self, private_key_sender: str,
                        public_key_sender: str,
                        recipient_address: str,
                        amount: float,
                        chain: list):

        # Verifica se a pessoa tem moedas necessarias
        public_key = Wallet.load_public_key_from_string(key_string=public_key_sender)
        address_sender = Wallet.generate_address(public_key)
        wallet_balance = Transaction.check_wallet_balance(chain, wallet_address=address_sender)

        if amount <= 0:
            raise TransactionError('Não é possivel realizar ransações negativas.',
            status_code=422)
        if int(amount) >= int(wallet_balance['balance']):
            raise TransactionError('Saldo insuficiente para realizar a transação.',
            status_code=422)

        print("Adicionando transição")
        self.sign_transaction(
            private_key=private_key_sender,
            public_key=public_key_sender,
            recipient_address=recipient_address, amount=amount
        )

        transaction_data = [{
            'address_sender': address_sender,
            'recipient_address': recipient_address,
            'amount': float(amount),
            'timestamp': str(datetime.datetime.now())
        }]

        self.save_transactions(transactions_file_path=self.transactions_file_path,
                                transaction_data=transaction_data)

        # previous_block = self.get_previous_block()
        # return previous_block['index'] + 1
        return True

    @staticmethod
    def calculate_balance_and_transactions(chain, wallet_address):
        """
        Calcula o saldo e compila uma lista de transações relevantes para um endereço de carteira.
        
        :param chain: Blockchain contendo os blocos e suas transações.
        :param wallet_address: Endereço da carteira para calcular saldo e transações.
        :return: Dicionário contendo o saldo e as transações.
        """
        balance = 0
        relevant_transactions = []

        for block in chain:
            block_timestamp = block.get('timestamp')
            for transaction in block.get('transactions', []):
                if wallet_address in (transaction.get('recipient_address'), transaction.get('address_sender')):
                    amount = transaction.get('amount', 0)

                    # Atualiza saldo baseado no tipo de transação
                    if transaction.get('recipient_address') == wallet_address:
                        balance += amount
                    else:
                        balance -= amount
                        amount *= -1

                    # Adiciona dados relevantes à transação
                    transaction_info = {
                        **transaction,
                        "timestamp": block_timestamp,
                        "amount": amount,
                    }
                    relevant_transactions.append(transaction_info)

        return {
            'balance': balance,
            'transactions': relevant_transactions
        }

    @staticmethod
    def check_wallet_balance(chain: List[Dict[str, Any]],
                                wallet_address: str) -> Dict[str, Any]:
        """
        Verifica o saldo e as transações de uma carteira.
        
        :param blockchain: Lista de blocos da blockchain.
        :param wallet_address: Endereço da carteira a ser verificado.
        :return: Dicionário contendo o saldo e as transações.
        """

        transactions_in_file = Transaction.load_transactions()

        file_transactions_data = Transaction.calculate_balance_and_transactions(
            [{'timestamp': t.get('timestamp'), 'transactions': [t]} for t in transactions_in_file],
            wallet_address
        )

        # Processar transações na blockchain
        blockchain_data = Transaction.calculate_balance_and_transactions(
            deepcopy(chain),  # Remove deepcopy se não for necessário
            wallet_address
        )

        # Combinar os resultados
        combined_balance = file_transactions_data['balance'] + blockchain_data['balance']
        combined_transactions = file_transactions_data['transactions'] + blockchain_data['transactions']

        # Ordenar transações por timestamp (opcional)
        combined_transactions.sort(key=lambda tx: tx.get('timestamp', 0))

        # Resultado final combinado
        final_data = {
            'balance': combined_balance,
            'transactions': combined_transactions
        }

        return final_data
