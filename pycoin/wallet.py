import base64
import hashlib

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey

# Tamanho truncado do endereço em bytes
ADDRESS_LENGTH = 16  # 16 bytes (128 bits)
CHECKSUM_LENGTH = 4  # Checksum de 4 bytes


class Wallet:
    def generate_strings_key_no_markers(self):
        """
        Gera uma chave privada e retorna apenas o conteúdo
        codificado em Base64 (sem os marcadores PEM).
        RETURNs:
        private_key_string, public_key_string
        """

        private_key, public_key = self.generate_keys()

        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        # Remove os marcadores e converte para uma única linha
        # Remove as linhas BEGIN/END e junta o conteúdo
        private_key_string = ''.join(private_key_pem.decode('utf-8').splitlines()[1:-1])
        public_key_string = ''.join(public_pem.decode('utf-8').splitlines()[1:-1])

        return (private_key_string, public_key_string, self.generate_address(public_key))

    @staticmethod
    def generate_keys():
        # Gerar chave privada e derivar a pública
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        return private_key, public_key

    @staticmethod
    def generate_address(public_key: EllipticCurvePrivateKey):
        """
        Gera um endereço menor a partir da chave pública, com checksum.
        """
        # Criar um endereço (hash da chave pública) no formato PEM
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        # Obter o hash da chave pública
        public_hash = hashlib.sha256(public_bytes).digest()

        # Truncar o hash para o comprimento do endereço
        address = public_hash[:ADDRESS_LENGTH]

        # Adicionar o checksum (últimos 4 bytes do SHA-256 do endereço)
        checksum = hashlib.sha256(address).digest()[:CHECKSUM_LENGTH]

        # Combinar endereço e checksum
        full_address = address + checksum

        # Codificar em base64 para facilitar o armazenamento
        encoded_address = base64.urlsafe_b64encode(full_address).decode()

        return encoded_address

    @staticmethod
    def is_validate_address(encoded_address):
        """
        Valida um endereço verificando o checksum.
        """
        try:
            # Decodificar o endereço
            full_address = base64.urlsafe_b64decode(encoded_address)

            # Separar endereço e checksum
            address = full_address[:ADDRESS_LENGTH]
            checksum = full_address[ADDRESS_LENGTH:]

            # Recalcular o checksum
            calculated_checksum = hashlib.sha256(address).digest()[:CHECKSUM_LENGTH]

            # Comparar checksums
            return checksum == calculated_checksum
        except Exception:
            return False

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

    @staticmethod
    def validate_key_pair(private_key, public_key):
        """
        Verifica se a chave pública corresponde à chave privada fornecida.

        :param private_key: A chave privada.
        :param public_key: A chave pública.
        :return: True se as chaves forem correspondentes, False caso contrário.
        """
        test_message = b'validate_keys'
        try:
            # Assina uma mensagem de teste
            signature = private_key.sign(test_message, ec.ECDSA(hashes.SHA256()))
            # Verifica a assinatura com a chave pública
            public_key.verify(signature, test_message, ec.ECDSA(hashes.SHA256()))
            return True
        except InvalidSignature:
            return False
