# node/routes/p2p.py
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel

from node.services.network_service import NetworkService
from node.storage.chain_repository import ChainRepository


# Models para validação
class HandshakeRequest(BaseModel):
    port: int


class BlockPayload(BaseModel):
    header: dict
    transactions: list
    hash: str
    height: int


router = APIRouter(prefix="/p2p", tags=["P2P"])

# Injeção de dependência resolvida via dependencies.py (evita circular import)
from node.dependencies import get_chain_repo, get_network


@router.post("/handshake")
def receive_handshake(
    req: HandshakeRequest,
    network: NetworkService = Depends(get_network)
):
    """Outro node está se apresentando."""
    network.add_peer("localhost", req.port)
    return {"status": "connected", "my_peers": list(network.peers)}


@router.post("/receive_block")
async def receive_block_from_peer(
    block_data: dict,  # Recebemos dict puro para flexibilidade
    background_tasks: BackgroundTasks,
    repo: ChainRepository = Depends(get_chain_repo),
    network: NetworkService = Depends(get_network)
):
    """
    Recebe um bloco minerado por outro nó.
    """
    block_hash = block_data['hash']

    # 1. Já tenho esse bloco?
    if repo.get_block(block_hash):
        return {"status": "ignored", "reason": "already_have"}

    # 2. Validação Rápida: O bloco se conecta ao meu último?
    last_hash = repo.get_last_block_hash()
    last_block = repo.get_block(last_hash)

    # CASO A: Encaixe perfeito (Append)
    # O bloco novo aponta para o meu último bloco
    if block_data['header']['prev_block_hash'] == last_hash:
        print(f"📥 Recebi bloco válido {block_data['height']} de um peer via P2P.")

        # Reconstrói objeto Block (simplificado)
        # Em produção, usaria um parser robusto Core.Block.from_dict(block_data)
        # Aqui vamos assumir que o save_block aceita o dict ou reconstruímos manualmente
        # (Para o tutorial, vamos assumir que você implementou Block.from_dict no Core)
        # block = Block.from_dict(block_data)
        # repo.save_block(block)

        # IMPORTANTE: Re-propagar para outros peers (Gossip)
        # background_tasks.add_task(network.broadcast_block, block_data)

        return {"status": "accepted"}

    # CASO B: Gap Detectado (Estou atrasado)
    # O bloco novo tem altura 50, mas eu estou no 40.
    elif block_data['height'] > last_block.height + 1:
        print(f"🐢 Estou atrasado! (Eu: {last_block.height}, Peer: {block_data['height']})")
        return {"status": "gap_detected", "action": "need_sync"}

    return {"status": "rejected"}
