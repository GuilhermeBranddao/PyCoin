from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from core.block import Block

# Importamos o app e as dependências para fazer o override
from node.app import app
from node.dependencies import get_chain_repo, get_mempool
from node.services.mempool_service import MempoolService
from node.storage.chain_repository import ChainRepository

# --- Fixtures de Integração ---


@pytest.fixture
def mock_repo():
    """
    Cria um Repositório Mockado para não sujar o disco real.
    """
    repo = MagicMock(spec=ChainRepository)

    # Configura o estado inicial: Já existe um bloco Gênesis
    genesis = Block.create_genesis_block()
    repo.get_last_block_hash.return_value = genesis.id
    repo.get_block.return_value = genesis

    # O método save_block não fará nada real, mas podemos verificar se foi chamado
    repo.save_block.return_value = True

    # Mock do UTXO (para cálculo de fees)
    repo.get_utxo.return_value = {'amount': 50}

    return repo


@pytest.fixture
def mock_mempool():
    """
    Mempool vazia ou controlada.
    """
    mempool = MagicMock(spec=MempoolService)
    mempool.get_candidate_transactions.return_value = []  # Sem txs pendentes por enquanto
    return mempool


@pytest.fixture
def client(mock_repo, mock_mempool):
    """
    Cria o TestClient do FastAPI com as dependências substituídas.
    """
    # 1. Override das dependências
    app.dependency_overrides[get_chain_repo] = lambda: mock_repo
    app.dependency_overrides[get_mempool] = lambda: mock_mempool

    with TestClient(app) as test_client:
        yield test_client

    # 2. Limpeza após o teste
    app.dependency_overrides.clear()


# --- Testes de Integração ---

class TestMiningAPI:

    def test_get_work_structure(self, client):
        """
        Testa se o endpoint /get_work retorna o JSON correto para o minerador.
        """
        miner_addr = "my_wallet_address"
        response = client.get(f"/mining/get_work?miner_address={miner_addr}")

        assert response.status_code == 200
        data = response.json()

        # Verifica contrato de dados
        assert "job_id" in data
        assert "target" in data
        assert "bits" in data
        assert "merkle_root" in data
        assert "prev_hash" in data

        # O job_id deve ser um hex válido (UUID)
        assert len(data["job_id"]) > 0

    @patch("core.blockchain.BlockchainRules.check_pow")
    def test_submit_work_success_flow(self, mock_check_pow, client, mock_repo, mock_mempool):
        """
        Testa o fluxo completo: Pegar Trabalho -> 'Minerar' -> Enviar.
        MOCKAMOS o check_pow para True, assim não precisamos gastar CPU no teste.
        """
        # 1. Configura o Mock para aceitar qualquer PoW
        mock_check_pow.return_value = True

        # 2. Passo A: Pegar o Trabalho (Get Work)
        response_get = client.get("/mining/get_work?miner_address=miner123")
        assert response_get.status_code == 200
        job_data = response_get.json()
        job_id = job_data["job_id"]

        # 3. Passo B: Simular o Minerador (Submit Work)
        # Como mockamos o check_pow, o nonce pode ser qualquer número
        payload = {
            "job_id": job_id,
            "nonce": 12345,
            "timestamp": job_data["timestamp"]
        }

        response_post = client.post("/mining/submit_work", json=payload)

        # 4. Asserts
        assert response_post.status_code == 200
        assert response_post.json()["status"] == "success"

        # Verifica se o bloco foi "salvo" no repositório
        mock_repo.save_block.assert_called_once()

        # Verifica se a mempool foi limpa (remove_transactions chamado)
        mock_mempool.remove_transactions.assert_called_once()

    def test_submit_work_invalid_job_id(self, client):
        """
        Tenta submeter um nonce para um job que não existe.
        """
        payload = {
            "job_id": "fake_job_uuid",
            "nonce": 999,
            "timestamp": 1234567890
        }
        response = client.post("/mining/submit_work", json=payload)

        assert response.status_code == 400
        assert "Job not found" in response.json()["detail"]

    @patch("core.blockchain.BlockchainRules.check_pow")
    def test_submit_work_invalid_pow(self, mock_check_pow, client):
        """
        Simula o cenário onde o minerador envia um nonce errado (hash alto).
        """
        # Força a validação do Core a falhar
        mock_check_pow.return_value = False

        # Precisamos de um Job válido primeiro para passar da checagem de "Job not found"
        r = client.get("/mining/get_work?miner_address=x")
        valid_job_id = r.json()["job_id"]

        payload = {
            "job_id": valid_job_id,
            "nonce": 0,
            "timestamp": 123
        }

        response = client.post("/mining/submit_work", json=payload)

        assert response.status_code == 400
        assert "Invalid Proof of Work" in response.json()["detail"]
