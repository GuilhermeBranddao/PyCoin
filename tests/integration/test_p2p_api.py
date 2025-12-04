from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from node.app import app
from node.dependencies import get_chain_repo, get_network

client = TestClient(app)


@pytest.fixture
def mock_network():
    mock = MagicMock()
    mock.peers = {"127.0.0.1:8001"}  # Simula que já temos um peer
    app.dependency_overrides[get_network] = lambda: mock
    return mock


@pytest.fixture
def mock_repo():
    mock = MagicMock()
    app.dependency_overrides[get_chain_repo] = lambda: mock
    return mock


def test_p2p_handshake(mock_network):
    """
    Testa se o node aceita conexão de um novo par.
    """
    payload = {"port": 9000}
    response = client.post("/p2p/handshake", json=payload)

    assert response.status_code == 200
    # Verifica se adicionou o peer com o host padrão (localhost do TestClient)
    # Nota: No TestClient o host remoto costuma ser 'testclient' ou 'localhost'
    mock_network.add_peer.assert_called()
    assert response.json()["status"] == "connected"


def test_receive_block_success_append(mock_repo, mock_network):
    """
    Cenário: Recebemos um bloco que se encaixa perfeitamente no nosso último.
    (Meu ultimo: Hash A, Height 10. Novo: Prev A, Height 11).
    """
    # 1. Mock do estado atual do banco
    mock_repo.get_block.return_value = None  # Não tenho esse bloco novo ainda
    mock_repo.get_last_block_hash.return_value = "hash_A"  # Meu topo atual

    # 2. Payload do Bloco Novo (Simplificado)
    block_payload = {
        "header": {
            "prev_block_hash": "hash_A",  # Encaixa perfeitamente
            "merkle_root": "root",
            "timestamp": 12345,
            "bits": 123,
            "nonce": 0,
            "version": 1
        },
        "transactions": [],
        "hash": "new_block_hash_B",
        "height": 11  # 10 + 1
    }

    # 3. Disparo
    response = client.post("/p2p/receive_block", json=block_payload)

    # 4. Asserts
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


def test_receive_block_gap_detected(mock_repo, mock_network):
    """
    Cenário: Recebemos um bloco muito a frente (Gap).
    (Meu ultimo: Height 10. Novo: Height 50).
    Deve retornar 'gap_detected'.
    """
    # Configura meu estado atual (Bloco 10)
    last_block_mock = MagicMock()
    last_block_mock.height = 10

    mock_repo.get_block.side_effect = lambda x: None if x == "block_50" else last_block_mock
    mock_repo.get_last_block_hash.return_value = "hash_10"
    # Quando o código pedir o bloco do hash_10, retorna o mock altura 10
    mock_repo.get_block.return_value = last_block_mock

    block_payload = {
        "header": {"prev_block_hash": "hash_49"},  # Não conheço esse hash
        "transactions": [],
        "hash": "block_50",
        "height": 50  # Gap enorme (10 -> 50)
    }

    response = client.post("/p2p/receive_block", json=block_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "gap_detected"
    assert data["action"] == "need_sync"

    # Limpeza
    app.dependency_overrides = {}
