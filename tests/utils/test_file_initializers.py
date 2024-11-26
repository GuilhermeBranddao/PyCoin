import json
from pathlib import Path

from pycoin.settings.config import Settings
from pycoin.utils.file_initializers import (
    initialize_blockchain_file,
    initialize_node_file,
    initialize_transaction_file,
)

settings = Settings()


def test_initialize_blockchain_file():
    test_blockchain_file = settings.TEST_BLOCKCHAIN_FILE

    if test_blockchain_file.exists():
        test_blockchain_file.unlink()

    assert not test_blockchain_file.exists(), "O arquivo de teste deve estar ausente antes da inicialização."

    initialize_blockchain_file(block_file_path=test_blockchain_file)

    assert test_blockchain_file.exists(), "O arquivo de blockchain deve ser criado após a inicialização."

    with open(test_blockchain_file, 'r', encoding='utf-8') as file:
        blockchain = json.load(file)

    list_keys = ['index', 'timestamp', 'proof',
                 'hash', 'previous_hash', 'transactions']

    assert all([key in list_keys for key in blockchain[0]]), "O arquivo deve conter um bloco gênesis após a inicialização."

    assert len(blockchain) == 1, "O arquivo de blockchain deve conter apenas o bloco gênesis."
    assert blockchain[0]["index"] == 0, "O índice do bloco gênesis deve ser 0."

    if test_blockchain_file.exists():
        test_blockchain_file.unlink()


settings = Settings()


def test_initialize_node_file():
    test_file_path = settings.TEST_NODES_FILE
    test_file = Path(test_file_path)

    if test_file.exists():
        test_file.unlink()

    assert not test_file.exists(), "O arquivo de nodes deve ser removido antes do teste."

    initialize_node_file(nodes_file_path=test_file)

    assert test_file.exists(), "O arquivo de nodes não foi criado."

    with open(test_file, 'r', encoding='utf-8') as file:
        nodes = json.load(file)

    expected_nodes = settings.LIST_NODE_VALID

    assert not set(nodes['nodes']).difference(set(expected_nodes)), "Os nodes no arquivo não correspondem aos esperados."

    if test_file.exists():
        test_file.unlink()


def test_initialize_transaction_file():
    test_file_path = settings.TEST_TRANSACTIONS_FILE
    test_file = Path(test_file_path)

    if test_file.exists():
        test_file.unlink()

    assert not test_file.exists(), "O arquivo de transações deve ser removido antes do teste."

    initialize_transaction_file(transaction_file_path=test_file)

    assert test_file.exists(), "O arquivo de transações não foi criado."

    with open(test_file, 'r', encoding='utf-8') as file:
        transactions = json.load(file)

    assert "transactions" in transactions, "O arquivo de transações deve conter a chave 'transactions'."
    assert len(transactions["transactions"]) == 0, "A lista de transações deve estar vazia inicialmente."

    if test_file.exists():
        test_file.unlink()
