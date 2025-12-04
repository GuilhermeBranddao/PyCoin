from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from core.transaction import Transaction
from node.app import app
from node.dependencies import get_mempool

# Criamos o cliente de teste reutilizável
client = TestClient(app)


@pytest.fixture
def mock_mempool():
    """
    Cria um Mock do serviço de Mempool.
    Intercepta chamadas para 'add_transaction' para não rodar lógica real.
    """
    mock = MagicMock()
    # Substitui a dependência real do FastAPI pelo nosso Mock
    app.dependency_overrides[get_mempool] = lambda: mock
    try:
        yield mock
    finally:
        # Limpa o override após o teste para não afetar outros
        app.dependency_overrides.pop(get_mempool, None)


def test_submit_valid_transaction(mock_mempool, identity):
    """
    Cenário: Enviar uma transação válida via JSON para o endpoint POST /tx/
    Resultado esperado: 201 Created e tx_id retornado.
    """
    # 1. Preparar dados (Identity vem do conftest.py)
    private_key, my_address = identity

    # Criamos o JSON payload similar ao que uma Wallet enviaria
    tx_payload = {
        "inputs": [
            {
                "prev_tx_id": "deadbeef" * 8,
                "output_index": 0,
                "public_key": "pubkey_placeholder",  # Na vida real seria a chave hex
                "signature": "signature_placeholder"
            }
        ],
        "outputs": [
            {"amount": 50, "address": "receiver_address_123"}
        ],
        "timestamp": 1234567890.0
    }

    # 2. Executar Request
    response = client.post("/tx/", json=tx_payload)

    # 3. Validar Resposta HTTP
    data = response.json()
    assert response.status_code == 201
    assert data["status"] == "accepted"
    assert "tx_id" in data

    # 4. Validar se o Service foi chamado corretamente
    # O endpoint deve ter convertido o JSON em objeto Transaction e chamado o mempool
    assert mock_mempool.add_transaction.called

    # Podemos inspecionar o argumento passado para o mempool
    args, _ = mock_mempool.add_transaction.call_args
    tx_obj = args[0]
    assert isinstance(tx_obj, Transaction)
    assert tx_obj.outputs[0].amount == 50


def test_submit_transaction_validation_error(mock_mempool):
    """
    Cenário: O MempoolService rejeita a transação (ex: assinatura inválida).
    Resultado esperado: 400 Bad Request.
    """
    # Configuramos o mock para lançar erro quando chamado
    mock_mempool.add_transaction.side_effect = ValueError("Assinatura inválida")

    tx_payload = {
        "inputs": [],
        "outputs": [{"amount": 10, "address": "addr"}],
        "timestamp": 12345.0
    }

    response = client.post("/tx/", json=tx_payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Assinatura inválida"

    # Limpa os overrides após o teste para não afetar outros
    app.dependency_overrides = {}
