from http import HTTPStatus

import pytest

from pycoin.transaction import Transaction


def generate_wallet_in_json(client):
    """
    Gera uma carteira usando o cliente fornecido.
    """
    response = client.get("wallet/generate_wallet")
    return response.json()


def create_transaction(sender_private_key, sender_public_key, recipient_address, amount):
    """
    Cria uma transação com os parâmetros fornecidos.
    """
    return Transaction(
        recipient_address=recipient_address,
        amount=amount,
        private_key_sender=sender_private_key,
        public_key_sender=sender_public_key,
    )

def test_gererate_wallet(client):
    response = client.get("wallet/generate_wallet")

    assert response.status_code == HTTPStatus.OK


def test_valid_keys(client):
    """
    Testa se a transação é válida com chaves válidas.
    """
    wallet_A = generate_wallet_in_json(client)
    wallet_B = generate_wallet_in_json(client)

    transaction = create_transaction(
        sender_private_key=wallet_A["private_key"],
        sender_public_key=wallet_A["public_key"],
        recipient_address=wallet_B["address"],
        amount=999,
    )

    assert transaction.sign_transaction()


def test_transaction_invalid_keys(client):
    """
    Testa se o erro é lançado quando o remetente e o destinatário são iguais.
    """
    wallet_A = generate_wallet_in_json(client)

    transaction = create_transaction(
        sender_private_key=wallet_A["private_key"],
        sender_public_key=wallet_A["public_key"],
        recipient_address=wallet_A["address"],
        amount=999,
    )

    # Verifica se o erro esperado é lançado
    with pytest.raises(ValueError, match="O remetente e o destinatário não podem ser iguais"):
        transaction.sign_transaction()


def test_transaction_same_sender_recipient(client):
    """
    Testa se a chave privada e chave pública não correspondem.
    """
    wallet_A = generate_wallet_in_json(client)
    wallet_B = generate_wallet_in_json(client)

    transaction = create_transaction(
        sender_private_key=wallet_B["private_key"],
        sender_public_key=wallet_A["public_key"],
        recipient_address=wallet_B["address"],  # O mesmo endereço como destinatário
        amount=999,
    )

    with pytest.raises(ValueError, match="Chave privada e chave pública não correspondem."):
        transaction.sign_transaction()


def test_validate_address(client):
    """
    Testa se o endereço do destinatário é valido.
    """
    wallet_A = generate_wallet_in_json(client)

    transaction = create_transaction(
        sender_private_key=wallet_A["private_key"],
        sender_public_key=wallet_A["public_key"],
        recipient_address="BYXVAtULLifhYEscI_AExqSxQIk=",
        amount=999,
    )

    with pytest.raises(ValueError, match="O endereço do destinatário é invalido."):
        transaction.sign_transaction()
