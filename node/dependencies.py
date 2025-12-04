# node/dependencies.py
import logging

from node.config import config
from node.services.mempool_service import MempoolService
from node.services.network_service import NetworkService
from node.storage.chain_repository import ChainRepository

logger = logging.getLogger(__name__)

# --- Instanciação dos Singletons ---
# Eles vivem aqui agora, isolados do app e das rotas
# Agora usam os caminhos configurados dinamicamente

chain_repo = ChainRepository(
    db_path=config.db_path,
    blocks_path=config.blocks_path
)
mempool_service = MempoolService(chain_repository=chain_repo)
network_service = NetworkService()

logger.info(f"ChainRepository inicializado com db_path={config.db_path}")
logger.info("NetworkService inicializado")

# --- Funções para Injeção de Dependência (FastAPI Depends) ---


def get_chain_repo() -> ChainRepository:
    """Dependency injection para ChainRepository"""
    return chain_repo


def get_mempool() -> MempoolService:
    """Dependency injection para MempoolService"""
    return mempool_service


def get_network() -> NetworkService:
    """Dependency injection para NetworkService"""
    return network_service
