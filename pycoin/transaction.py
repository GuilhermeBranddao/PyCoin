import hashlib

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


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
        self.private_key = self.load_private_key_from_string(private_key_sender)
        self.public_key = self.load_public_key_from_string(public_key_sender)

    @staticmethod
    def load_private_key_from_string(key_string):
        """
        Carrega uma chave privada de uma string simplificada (sem marcações BEGIN/END)

        para o formato PEM e a converte em um objeto.
        :param key_string: Chave privada em uma única linha (sem marcações BEGIN/END).
        :return: Objeto da chave privada.
        """
        try:
            pem_formatted_key = (
                '-----BEGIN PRIVATE KEY-----\n'
                + '\n'.join(key_string[i : i + 64] for i in range(0, len(key_string), 64))
                + '\n-----END PRIVATE KEY-----'
            )

            private_key = serialization.load_pem_private_key(
                pem_formatted_key.encode('utf-8'), password=None
            )
            return private_key
        except Exception as e:
            print(f'Erro ao carregar chave privada: {e}')
            return None

    @staticmethod
    def load_public_key_from_string(key_string):
        """
        Carrega uma chave pública de uma string simplificada (sem marcações BEGIN/END)

        para o formato PEM e a converte em um objeto.
        :param key_string: Chave pública em uma única linha (sem marcações BEGIN/END).
        :return: Objeto da chave pública.
        """
        try:
            pem_formatted_key = (
                '-----BEGIN PUBLIC KEY-----\n'
                + '\n'.join(key_string[i : i + 64] for i in range(0, len(key_string), 64))
                + '\n-----END PUBLIC KEY-----'
            )

            public_key = serialization.load_pem_public_key(
                pem_formatted_key.encode('utf-8')
            )
            return public_key
        except Exception as e:
            print(f'Erro ao carregar chave pública: {e}')
            return None

    def sign_transaction(self):
        """
        Assina a transação usando a chave privada do remetente.

        :param private_key: A chave privada do remetente.
        :param public_key_sender: A chave pública correspondente.
        """
        self.sender = self.get_address_from_public_key()

        if not self.validate_key_pair():
            raise ValueError('Chave privada e chave pública não correspondem.')

        if self.sender == self.recipient_address:
            raise ValueError('O remetente e o destinatário não podem ser iguais.')

        transaction_data = self._get_transaction_data()
        self.signature = self.private_key.sign(
            transaction_data, ec.ECDSA(hashes.SHA256())
        )

        if not self.verify_signature():
            raise ValueError('Transação inválida! A assinatura não corresponde.')

    def get_address_from_public_key(self):
        """
        Gera um endereço simplificado (hash SHA-256) a partir de uma chave pública.

        :param public_key: A chave pública.
        :return: O endereço gerado como uma string hexadecimal.
        """
        public_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return hashlib.sha256(public_bytes).hexdigest()

    def validate_key_pair(self):
        """
        Verifica se a chave pública corresponde à chave privada fornecida.

        :param private_key: A chave privada.
        :param public_key: A chave pública.
        :return: True se as chaves forem correspondentes, False caso contrário.
        """
        test_message = b'validate_keys'
        try:
            # Assina uma mensagem de teste
            signature = self.private_key.sign(test_message, ec.ECDSA(hashes.SHA256()))
            # Verifica a assinatura com a chave pública
            self.public_key.verify(signature, test_message, ec.ECDSA(hashes.SHA256()))
            return True
        except InvalidSignature:
            return False

    def verify_signature(self):
        """
        Verifica a assinatura da transação usando a chave pública do remetente.

        :param public_key: A chave pública do remetente.
        :return: True se a assinatura for válida, False caso contrário.
        """
        transaction_data = self._get_transaction_data(
            self.sender, self.recipient_address, self.amount
        )

        try:
            self.public_key.verify(
                self.signature, transaction_data, ec.ECDSA(hashes.SHA256())
            )
            return True
        except InvalidSignature:
            return False

    @staticmethod
    def _get_transaction_data(sender, recipient_address, amount):
        """
        Concatena os dados da transação (sender, recipient, amount) em bytes

        com delimitadores.
        :return: Dados da transação em formato binário.
        """
        transaction_data = f'{sender}|{recipient_address}|{amount}'
        return transaction_data.encode('utf-8')

    @staticmethod
    def _decode_transaction_data(transaction_data):
        """
        Decodifica os dados da transação de volta para sender, recipient e amount.
        :param transaction_data: Dados binários da transação.
        :return: Um dicionário com as informações da transação.
        """
        decoded_data = transaction_data.decode('utf-8')
        sender, recipient_address, amount = decoded_data.split('|')

        return {
            'sender': sender,
            'recipient_address': recipient_address,
            'amount': float(amount),
        }
