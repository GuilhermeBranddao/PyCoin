from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from pycoin.wallet import Wallet

# Tamanho truncado do endereço em bytes
ADDRESS_LENGTH = 16  # 16 bytes (128 bits)
CHECKSUM_LENGTH = 4  # Checksum de 4 bytes


class Transaction:
    def __init__(self, recipient_address, amount, private_key_sender, public_key_sender):
        """
        Inicializa uma nova transação.

        :param private_key_sender chave do sender
        :param public_key_sender chave do sender
        :param recipient: O endereço do destinatário.
        :param amount: O valor a ser transferido.
        """
        self.recipient_address = recipient_address
        self.amount = amount
        self.private_key = Wallet.load_private_key_from_string(private_key_sender)
        self.public_key = Wallet.load_public_key_from_string(public_key_sender)

    def sign_transaction(self):
        """
        Assina a transação usando a chave privada do remetente.

        :param private_key: A chave privada do remetente.
        :param public_key_sender: A chave pública correspondente.
        """
        self.address_sender = Wallet.generate_address(public_key=self.public_key)

        if not Wallet.validate_key_pair(private_key=self.private_key,
                                      public_key=self.public_key):
            raise ValueError('Chave privada e chave pública não correspondem.')

        if self.address_sender == self.recipient_address:
            raise ValueError('O remetente e o destinatário não podem ser iguais.')

        if not Wallet.is_validate_address(self.recipient_address):
            raise ValueError('O endereço do destinatário é invalido.')

        transaction_data = self._get_transaction_data(
            self.address_sender, self.recipient_address, self.amount
        )
        self.signature = self.private_key.sign(
            transaction_data, ec.ECDSA(hashes.SHA256())
        )

        if self.verify_signature():
            return True
        else:
            raise ValueError('Transação inválida! A assinatura não corresponde.')

    def verify_signature(self):
        """
        Verifica a assinatura da transação usando a chave pública do remetente.

        :param public_key: A chave pública do remetente.
        :return: True se a assinatura for válida, False caso contrário.
        """
        transaction_data = self._get_transaction_data(
            self.address_sender, self.recipient_address, self.amount
        )

        try:
            self.public_key.verify(
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
