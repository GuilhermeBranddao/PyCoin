import pytest
from unittest.mock import AsyncMock, patch
from node.services.network_service import NetworkService

@pytest.fixture
def network():
    return NetworkService(my_port=8000)

class TestNetworkService:

    def test_add_peer_logic(self, network):
        # Adicionar peer normal
        assert network.add_peer("localhost", 8001) is True
        assert "http://localhost:8001" in network.peers
        
        # Não deve adicionar duplicado
        assert network.add_peer("localhost", 8001) is False
        
        # Não deve adicionar a si mesmo
        assert network.add_peer("localhost", 8000) is False

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    async def test_perform_handshake_success(self, mock_post, network):
        """Testa se ele chama o endpoint correto do peer alvo"""
        target = "http://localhost:9000"
        
        result = await network.perform_handshake(target)
        
        assert result is True
        assert target in network.peers
        mock_post.assert_called_with(
            f"{target}/p2p/handshake", 
            json={"port": 8000}
        )

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    async def test_broadcast_block(self, mock_post, network):
        """Testa se ele itera sobre todos os peers"""
        # Adiciona 2 peers
        network.peers.add("http://p1:8000")
        network.peers.add("http://p2:8000")
        
        block_data = {"hash": "abc", "height": 10}
        
        await network.broadcast_block(block_data)
        
        # Deve ter chamado post 2 vezes
        assert mock_post.call_count == 2
        # Verifica se marcou como conhecido para evitar loop
        assert "abc" in network.known_blocks