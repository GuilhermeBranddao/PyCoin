import hashlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


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

        return (private_key_string, public_key_string, self.get_address(public_key))

    @staticmethod
    def generate_keys():
        # Gerar chave privada e derivar a pública
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        return private_key, public_key

    @staticmethod
    def get_address(public_key):
        # Criar um endereço (hash da chave pública) no formato PEM
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        # address = hashes.Hash(hashes.SHA256())
        # address.update(public_bytes)
        # return address.finalize().hex()
        return hashlib.sha256(public_bytes).hexdigest()
