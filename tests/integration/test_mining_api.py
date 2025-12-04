from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from core.block import Block

# Importamos a aplicação real e os tipos necessários
from node.app import app
from node.dependencies import get_chain_repo, get_mempool

# --- Mocks para as Dependências ---


class MockChainRepository:
    """Simula o banco de dados em memória"""
    def __init__(self):
        self.blocks = {}
        # Cria um genesis fake para começar
        genesis = Block.create_genesis_block()
        self.save_block(genesis)

    def get_last_block_hash(self):
        # Retorna o hash do último bloco inserido (simulação simples)
        if not self.blocks: return None
        # Pega o último values() inserido (Python dicts são ordenados em 3.7+)
        return list(self.blocks.values())[-1].id

    def get_block(self, block_hash):
        return self.blocks.get(block_hash)

    def save_block(self, block):
        self.blocks[block.id] = block

    def get_utxo(self, tx_id, index):
        # Retorna um valor fictício para calcular taxas
        return {'amount': 50, 'address': 'someone'}


class MockMempoolService:
    """Simula a Mempool"""
    def __init__(self):
        self.transactions = []

    def get_candidate_transactions(self):
        # Retorna lista vazia ou algumas txs dummy
        return self.transactions

    def remove_transactions(self, txs):
        pass

# --- Configuração do TestClient ---


@pytest.fixture
def client():
    # 1. Instancia os Mocks
    mock_repo = MockChainRepository()
    mock_mempool = MockMempoolService()

    # 2. Sobrescreve as dependências da App FastAPI
    app.dependency_overrides[get_chain_repo] = lambda: mock_repo
    app.dependency_overrides[get_mempool] = lambda: mock_mempool

    # 3. Retorna o cliente de teste
    with TestClient(app) as test_client:
        yield test_client

    # Limpeza
    app.dependency_overrides = {}

# --- Testes de Integração ---


def test_get_work_endpoint(client):
    """
    Testa se o endpoint /mining/get_work retorna um Job válido.
    """
    response = client.get("/mining/get_work", params={"miner_address": "my_wallet_123"})

    assert response.status_code == 200
    data = response.json()

    # Verifica contrato da resposta
    assert "job_id" in data
    assert "target" in data
    assert "prev_hash" in data
    assert "bits" in data

    # Verifica se o target é um hex válido
    assert data["target"].startswith("0x")


def test_submit_work_success(client):
    """
    Testa o fluxo completo: Pegar trabalho -> Resolver (Simulado) -> Enviar.
    """
    # 1. Pega o trabalho
    res_work = client.get("/mining/get_work", params={"miner_address": "miner1"})
    work_data = res_work.json()
    job_id = work_data["job_id"]

    # 2. Simula a mineração (Mockamos a validação de PoW para não fritar a CPU no teste)
    # Precisamos 'patchar' o validador de PoW dentro do endpoint submit_work
    # O caminho do patch deve ser onde a classe é IMPORTADA no arquivo mining.py
    with patch("core.blockchain.BlockchainRules.check_pow") as mock_check_pow:
        mock_check_pow.return_value = True  # Dizemos: "Sim, o PoW é válido!"

        payload = {
            "job_id": job_id,
            "nonce": 12345,     # Nonce qualquer, já que mockamos a validação
            "timestamp": work_data["timestamp"]
        }

        # 3. Envia o trabalho
        res_submit = client.post("/mining/submit_work", json=payload)

        assert res_submit.status_code == 200
        assert res_submit.json()["status"] == "success"
        assert "block_hash" in res_submit.json()


def test_submit_work_invalid_job_id(client):
    """Testa submissão com Job ID inexistente"""
    payload = {
        "job_id": "fake_id_999",
        "nonce": 1,
        "timestamp": 123456
    }
    res = client.post("/mining/submit_work", json=payload)
    assert res.status_code == 400
    assert "Job not found" in res.json()["detail"]


def test_submit_work_invalid_pow(client):
    """Testa rejeição de trabalho inválido (PoW incorreto)"""
    # Pega trabalho real para ter ID válido
    res_work = client.get("/mining/get_work", params={"miner_address": "miner1"})
    job_id = res_work.json()["job_id"]

    # NÃO fazemos patch do check_pow aqui (ou forçamos False).
    # Com nonce aleatório, a chance de acertar é nula, então deve falhar.

    payload = {
        "job_id": job_id,
        "nonce": 0,  # Provavelmente errado
        "timestamp": res_work.json()["timestamp"]
    }

    res = client.post("/mining/submit_work", json=payload)
    assert res.status_code == 400
    assert "Invalid Proof of Work" in res.json()["detail"]
