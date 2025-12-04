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
