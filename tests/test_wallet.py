from http import HTTPStatus

import pytest

from pycoin.settings import Settings
from pycoin.transaction import Transaction

settings = Settings()


def generate_wallet_in_json(client):
    """
    Gera uma carteira usando o cliente fornecido.
    """
    response = client.get("wallet/generate_wallet")
    return response.json()


def create_transaction():
    """
    Cria uma transação com os parâmetros fornecidos.
    """
    return Transaction()


def test_gererate_wallet(client):
    response = client.get("wallet/generate_wallet")

    assert response.status_code == HTTPStatus.OK


def test_add_transaction(client):
    wallet_A = generate_wallet_in_json(client)
    wallet_B = generate_wallet_in_json(client)

    data = {
        "private_key_sender": wallet_A["private_key"],
        "public_key_sender": wallet_A["public_key"],
        "recipient_address": wallet_B["address"],
        "amount": 100.0
    }
    response = client.post("wallet/add_transaction",
                          json=data)

    # FIXME: Essa transação não deveria ocorrer com sucesso
    assert response.status_code == HTTPStatus.OK
    assert response.json().get("message") == "Nova transação adicionada"


def test_save_transaction():
    """
    Testa todas as possibilidades de manuseio de dados das transações
    """

    test_transactions_file_path = settings.TEST_TRANSACTION_FILENAME

    test_transaction_data = {
            "address_sender": "pum7mQtJqClnNuMIPxCwZSWJkE4=",
            "recipient_address": "G7j6UydY3hNM-SzpRxyzIJf1I3M=",
            "amount": 111.1
        }

    transaction = Transaction()
    is_save_bool = transaction.save_transactions(test_transactions_file_path,
                                  test_transaction_data)

    test_load_transactions = transaction.load_transactions(test_transactions_file_path)
    transaction.clear_transactions(test_transactions_file_path)
    test_check_load_transactions = transaction.load_transactions(test_transactions_file_path)

    assert is_save_bool
    assert len(test_load_transactions) > 0
    assert len(test_check_load_transactions) == 0


def test_error_switch_keys_public_per_private():
    """
    Os usuario podem a chave publica pela privada e vice versa
    """
    pass


def test_valid_keys(client):
    """
    Testa se a transação é válida com chaves válidas.
    """
    wallet_A = generate_wallet_in_json(client)
    wallet_B = generate_wallet_in_json(client)

    transaction = Transaction()

    assert transaction.sign_transaction(
        public_key=wallet_A["public_key"],
        private_key=wallet_A["private_key"],
        recipient_address=wallet_B["address"],
        amount=999.6)


def test_transaction_invalid_keys(client):
    """
    Testa se o erro é lançado quando o remetente e o destinatário são iguais.
    """
    wallet_A = generate_wallet_in_json(client)
    transaction = Transaction()

    # Verifica se o erro esperado é lançado
    with pytest.raises(ValueError, match="O remetente e o destinatário não podem ser iguais"):
        transaction.sign_transaction(public_key=wallet_A["public_key"],
                                     private_key=wallet_A["private_key"],
                                     recipient_address=wallet_A["address"],
                                     amount=999.0)


def test_transaction_same_sender_recipient(client):
    """
    Testa se a chave privada e chave pública não correspondem.
    """
    wallet_A = generate_wallet_in_json(client)
    wallet_B = generate_wallet_in_json(client)

    transaction = Transaction()

    with pytest.raises(ValueError, match="Chave privada e chave pública não correspondem."):
        transaction.sign_transaction(public_key=wallet_B["public_key"],
                                     private_key=wallet_A["private_key"],
                                     recipient_address=wallet_B["address"],
                                     amount=999.0)


def test_validate_address(client):
    """
    Testa se o endereço do destinatário é valido.
    """
    wallet_A = generate_wallet_in_json(client)

    transaction = Transaction()

    with pytest.raises(ValueError, match="O endereço do destinatário é invalido."):
        transaction.sign_transaction(public_key=wallet_A["public_key"],
                                     private_key=wallet_A["private_key"],
                                     recipient_address="BYXVAtULLifhYEscI_AExqSxQIk=",
                                     amount=999.0)
