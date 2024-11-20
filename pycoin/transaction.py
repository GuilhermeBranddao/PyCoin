import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey

from pycoin.blockchain.tool_blockchain import (
    load_blockchain,
)
from pycoin.settings import Settings
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

        self.transactions_file_path = settings.TRANSACTION_FILENAME

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
    def save_transactions(transactions_file_path: Path, transaction_data: Dict):
        """
        Salva as transações do arquivo JSON, mantendo a estrutura básica.
        """
        print('Salvando transações')

        # Inicializa a estrutura de dados para armazenar transações
        transactions = {"transactions": []}

        if not isinstance(transactions_file_path, Path):
            raise ValueError("O parâmetro block_file_path deve ser um objeto do tipo Path.")

        try:
            with open(transactions_file_path, 'r', encoding='utf-8') as file:
                transactions = json.load(file)
        except FileNotFoundError:
            # Arquivo não existe, inicializa com a estrutura padrão
            print(f"{transactions_file_path} não encontrado, criando um novo arquivo.")
            transactions_file_path.parent.mkdir(parents=True, exist_ok=True)
            transactions_file_path.touch()
        except json.JSONDecodeError:
            # Arquivo vazio ou com dados inválidos, inicia a estrutura padrão
            print(f"{transactions_file_path} contém dados inválidos, sobrescrevendo com uma estrutura válida.")
            return False

        # Adiciona a nova transação ao conjunto de transações existentes
        transactions["transactions"].append(transaction_data)

        # Salva as transações atualizadas de volta ao arquivo
        with open(transactions_file_path, 'w', encoding='utf-8') as file:
            json.dump(transactions, file, indent=4)

        return True

    @staticmethod
    def load_transactions(transactions_file_path: Path):
        """
        Carrega todas as transações do arquivo JSON, mantendo a estrutura básica.
        """
        print("Carregando transações")
        if not isinstance(transactions_file_path, Path):
            raise ValueError("O parâmetro block_file_path deve ser um objeto do tipo Path.")

        transactions_file_path.parent.mkdir(parents=True, exist_ok=True)
        transactions_file_path.touch()

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
            except:
                print("Erro desconhecido")

        # Cria
        # FIXME: Isso aqui é uma gambiarra só pra fazer o código rodar
        # O que está acontecendo é que se não tiver o arquivo o load não encontra e dá um erro
        Transaction.save_transactions(transactions_file_path,
                                      transaction_data=[])

    @staticmethod
    def clear_transactions(transactions_file_path: str):
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

    def add_transaction(self, private_key_sender: str, public_key_sender: str,
                        recipient_address: str, amount: float):

        # Verifica se a pessoa tem moedas necessarias
        public_key = Wallet.load_public_key_from_string(key_string=public_key_sender)
        address_sender = Wallet.generate_address(public_key)
        wallet_balance = Transaction.check_wallet_balance(blockchain=load_blockchain(
            block_file_path=settings.BLOCK_FILENAME),
        wallet_address=address_sender)

        if wallet_balance['balance'] >= amount:
            raise ValueError('Saldo insuficiente para realizar a transação.')

        print("Adicionando transição")
        self.sign_transaction(
            private_key=private_key_sender,
            public_key=public_key_sender,
            recipient_address=recipient_address, amount=amount
        )

        public_key = Wallet.load_public_key_from_string(key_string=public_key_sender)
        address_sender = Wallet.generate_address(public_key=public_key)

        transaction_data = {
            'address_sender': address_sender,
            'recipient_address': recipient_address,
            'amount': float(amount),
        }

        self.save_transactions(transactions_file_path=self.transactions_file_path,
                                transaction_data=transaction_data)

        # previous_block = self.get_previous_block()
        # return previous_block['index'] + 1
        return True

    @staticmethod
    def check_wallet_balance(blockchain: List[Dict[str, Any]], wallet_address: str) -> Dict[str, Any]:
        """
        Verifica o saldo e as transações de uma carteira.
        
        :param blockchain: Lista de blocos da blockchain.
        :param wallet_address: Endereço da carteira a ser verificado.
        :return: Dicionário contendo o saldo e as transações.
        """
        balance = 0
        transactions = []
        blockchain = deepcopy(blockchain)
        for block in blockchain:
            for transaction in block.get('transactions', []):
                if wallet_address in (transaction.get('recipient_address'), transaction.get('address_sender')):
                    amount = transaction.get('amount', 0)
                    if transaction.get('recipient_address') == wallet_address:
                        balance += amount
                    else:
                        balance -= amount
                        amount *= -1

                    # Adiciona dados relevantes à transação
                    transaction_info = {
                        **transaction,
                        "timestamp": block.get('timestamp'),
                        "amount": amount
                    }
                    transactions.append(transaction_info)

        return {
            'balance': balance,
            'transactions': transactions
        }
