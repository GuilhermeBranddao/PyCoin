# node/app.py
"""
PyCoin Node - Servidor FastAPI para gerenciar blockchain
Suporta múltiplas instâncias isoladas (diferentes portas)
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from node.config import config
from node.dependencies import get_chain_repo, get_network
from node.routes import mining, p2p, tx

# --- Logging ---
logger = logging.getLogger(__name__)


# --- Lifespan Context Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação (startup e shutdown)
    """
    # --- STARTUP ---
    logger.info(f"🚀 Node iniciado na porta {config.port}")
    logger.info(f"   Modo: {'Genesis' if config.is_genesis_node else 'Peer'}")
    logger.info(f"   DB: {config.db_path}")

    # Inicializa o repositório
    repo = get_chain_repo()
    logger.info(f"✅ ChainRepository carregado com {len(repo.blocks_dir)} blocos")

    # Se for um peer (não é Genesis), tenta conectar ao node 8000
    if not config.is_genesis_node:
        logger.info("📡 Iniciando handshake com node Genesis (porta 8000)...")
        try:
            # Será feito na rota de startup
            pass
        except Exception as e:
            logger.warning(f"⚠️ Falha no handshake inicial: {e}")

    yield  # O servidor roda aqui

    # --- SHUTDOWN ---
    logger.info("🛑 Node desligando...")
    # Aqui você pode fechar conexões de banco de dados, etc.


# --- Inicialização da App ---
app = FastAPI(
    title="PyCoin Node",
    description=f"Node na porta {config.port}",
    version="1.0.0",
    lifespan=lifespan
)

# --- Registro de Rotas ---
app.include_router(tx.router, tags=["Transactions"])  # prefix="/tx",
app.include_router(mining.router, tags=["Mining"])  # prefix="/mining",
app.include_router(p2p.router, tags=["P2P"])  # prefix="/p2p",


# --- Health Check ---
@app.get("/health", tags=["Health"])
async def health_check():
    """Verifica se o node está online"""
    return {
        "status": "online",
        "port": config.port,
        "is_genesis": config.is_genesis_node,
        "blocks_count": len(get_chain_repo().blocks_dir)
    }


@app.on_event("startup")
async def startup_event():
    """Evento de startup para conectar ao Genesis se necessário"""
    if not config.is_genesis_node:
        logger.info("Realizando handshake com Genesis node...")
        try:
            network = get_network()
            await network.perform_handshake("http://localhost:8000")
        except Exception as e:
            logger.error(f"Falha no handshake: {e}")


# --- Entry Point ---
if __name__ == "__main__":
    uvicorn.run(
        "node.app:app",
        host="0.0.0.0",
        port=config.port,
        reload=False,  # Desative em produção com múltiplas instâncias
        log_level="info"
    )
