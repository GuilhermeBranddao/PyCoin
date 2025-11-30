from http import HTTPStatus


def test_start_mining_success(client):
    # Faz a requisição GET para a rota de mineração
    response = client.get("miner/start_mining")

    # Verifica se a resposta foi bem-sucedida
    assert response.status_code == HTTPStatus.OK

    data = response.json()
    assert "message" in data, "Resposta deve conter a chave 'message'"
    assert "new_block" in data["message"], "Resposta deve conter o bloco minerado"

    new_block = data["message"]["new_block"]

    # Verifica se o bloco minerado tem os campos essenciais
    assert "index" in new_block
    assert "hash" in new_block
    assert "proof" in new_block
    assert "previous_hash" in new_block
    assert "transactions" in new_block
