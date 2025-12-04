"""
Configuração centralizada para o Node
"""
import logging
import sys
from pathlib import Path

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# --- Detecção de Porta ---
def get_port_from_args(default: int = 8000) -> int:
    """
    Extrai a porta do argumento de linha de comando.
    Uso: python node/app.py 8001
    
    Args:
        default: porta padrão se nenhuma for fornecida
        
    Returns:
        int: porta a usar
    """
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            if 1 <= port <= 65535:
                logger.info(f"Porta detectada via argumento: {port}")
                return port
            else:
                logger.warning(f"Porta inválida: {port}. Usando padrão: {default}")
                return default
        except ValueError:
            logger.warning(f"Argumento não é uma porta válida: {sys.argv[1]}. Usando padrão: {default}")
            return default

    logger.info(f"Usando porta padrão: {default}")
    return default


# --- Configurações do Node ---
class NodeConfig:
    """Configuração imutável do Node"""

    def __init__(self, port: int = 8000):
        self.port = port
        self.is_genesis_node = (port == 8000)

        # Caminhos de armazenamento isolados por porta
        self.data_dir = Path(f"./data/node_{port}")
        self.db_path = str(self.data_dir / "chainstate")
        self.blocks_path = str(self.data_dir / "blocks")

        # Criar diretórios se não existirem
        self._ensure_directories()

    def _ensure_directories(self):
        """Garante que os diretórios necessários existem"""
        Path(self.db_path).mkdir(parents=True, exist_ok=True)
        Path(self.blocks_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Diretórios verificados para porta {self.port}")

    def __repr__(self):
        return (
            f"NodeConfig(port={self.port}, "
            f"is_genesis={self.is_genesis_node}, "
            f"db_path={self.db_path})"
        )


# --- Instância Global (Singleton) ---
PORT = get_port_from_args()
config = NodeConfig(port=PORT)

logger.info(f"Configuração do Node: {config}")


# --- CONSTANTES DE CONSENSO (Hardcoded Rules) ---
# Todos os nós da rede DEVEM concordar com estes valores.

TARGET_BLOCK_TIME = 180            # 3 minutos em segundos
DIFFICULTY_ADJUSTMENT_INTERVAL = 10  # A cada 10 blocos recalculamos a dificuldade
                                   # (No Bitcoin é 2016 blocos)

# Dificuldade Inicial (Bits Compactos)
# 0x1d00ffff é a Dificuldade Real do Bitcoin, um valor alto padrão para testes
# GENESIS_BITS = 0x1d00ffff

# Dificuldade de Desenvolvimento - Muito Fácil
# Explicação do 0x207fffff:
# 0x20 (32 bytes de exponente)
# 0x7fffff (coeficiente máximo)
# Resultado: O Target vira um número gigantesco. Quase qualquer hash serve.
# GENESIS_BITS = 0x207fffff

# Dificuldade Inicial Ajustada (Target menor = Mais difícil)
# 0x207fffff = Muito Fácil (Instantâneo)
# 0x1d00ffff = Padrão Bitcoin CPU (Difícil)
# 0x1e00ffff = Intermediário (Bom para testes)
GENESIS_BITS = 0x1e00ffff

# Configuração da Wallet
NODE_URL = "http://localhost:8000"
KEY_FILE = "my_private_key_user_2.pem"

# Endereço onde você quer receber a recompensa (pode ser qualquer string por enquanto)
MINER_ADDRESS = "aff5cf59242bab8cb77ff135eef3b923ee7dd97d2b4fce91801e11c86459b897"
# "b117480ce46bf5ff0950c3c32acdbaa828e44ffa243d2a045a6f28006fef93f0"
# 30265c2a6625100624496cb75f24ae583c78cb517f59c82327a3c4e1a1378216


BLOCK_REWARD = 50  # Recompensa fixa por bloco (Halving viria aqui no futuro)
