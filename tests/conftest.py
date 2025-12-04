import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


@pytest.fixture
def identity():
    """
    Gera uma identidade (Par de chaves) temporária para os testes.
    Retorna (private_key, address_string).
    """
    private_key = ec.generate_private_key(ec.SECP256K1())
    public_key = private_key.public_key()

    # Gera o endereço (simulado como hash da chave pública para simplificar)
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    digest = hashes.Hash(hashes.SHA256())
    digest.update(pub_bytes)
    address = digest.finalize().hex()

    return private_key, address
