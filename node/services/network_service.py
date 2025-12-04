# node/services/network.py
import asyncio
from typing import Set

import httpx


class NetworkService:
    def __init__(self, my_port: int = 8000):
        self.peers: Set[str] = set()
        self.my_port = my_port
        # Evita propagar o mesmo bloco duas vezes (loop infinito na rede)
        self.known_blocks: Set[str] = set()

    def add_peer(self, host: str, port: int):
        """Registra um novo amigo na rede"""
        peer_url = f"http://{host}:{port}"
        # Não adiciona a si mesmo
        if port != self.my_port and peer_url not in self.peers:
            self.peers.add(peer_url)
            print(f"📡 Peer adicionado: {peer_url}")
            return True
        return False

    async def broadcast_block(self, block_data: dict):
        """
        Gossip Protocol: Espalha o bloco para todos os peers.
        """
        block_hash = block_data['hash']
        if block_hash in self.known_blocks:
            return  # Já vi, não repasso

        self.known_blocks.add(block_hash)
        print(f"📣 Propagando bloco {block_hash[:8]} para {len(self.peers)} peers...")

        async with httpx.AsyncClient() as client:
            tasks = []
            for peer in self.peers:
                tasks.append(self._send_block(client, peer, block_data))

            # Dispara tudo em paralelo (Fire and Forget)
            await asyncio.gather(*tasks)

    async def _send_block(self, client, peer, block_data):
        try:
            # Envia para a rota de recepção do peer
            await client.post(f"{peer}/p2p/receive_block", json=block_data, timeout=2.0)
        except Exception as e:
            print(f"⚠️ Falha ao entregar para {peer}: {e}")
            # Se falhar muito, poderíamos remover o peer da lista aqui

    async def perform_handshake(self, target_node_url: str):
        """
        Conecta-se a um node existente e diz: "Oi, estou aqui na porta X, me adicione".
        """
        my_url = f"http://localhost:{self.my_port}"  # Simplificação para localhost
        try:
            async with httpx.AsyncClient() as client:
                # 1. Avisa que existo
                await client.post(f"{target_node_url}/p2p/handshake", json={"port": self.my_port})
                # 2. Adiciona ele na minha lista
                # (Assumindo localhost para simplificar o teste local)
                target_port = int(target_node_url.split(":")[-1])
                self.add_peer("localhost", target_port)
                print(f"🤝 Handshake realizado com {target_node_url}")

                # 3. Gatilho de Sincronização (Discutiremos no passo 3)
                return True
        except Exception as e:
            print(f"❌ Erro no handshake com {target_node_url}: {e}")
            return False
