import time
from typing import Optional, Tuple

from core.block import Block, BlockHeader

# --- CONSTANTES DE CONSENSO (Hardcoded Rules) ---
# Todos os nós da rede DEVEM concordar com estes valores.

TARGET_BLOCK_TIME = 180            # 3 minutos em segundos
DIFFICULTY_ADJUSTMENT_INTERVAL = 10 # A cada 10 blocos recalculamos a dificuldade
                                   # (No Bitcoin é 2016 blocos)

# Dificuldade Inicial (Bits Compactos)
# 0x1d00ffff é um valor alto padrão para testes (fácil de minerar)
GENESIS_BITS = 0x1d00ffff 

class DifficultyEngine:
    """
    Gerencia a matemática por trás do ajuste de dificuldade.
    Usa representação compacta 'bits' (similar ao IEEE floating point) para targets de 256 bits.
    """

    @staticmethod
    def calculate_next_work_required(last_block: Block, 
                                     epoch_start_block: Block) -> int:
        """
        Calcula os 'bits' para o próximo bloco.
        Só muda se fecharmos o intervalo (height % INTERVAL == 0).
        """
        
        # 1. Se não for hora de ajustar, mantém a dificuldade anterior
        if (last_block.height + 1) % DIFFICULTY_ADJUSTMENT_INTERVAL != 0:
            return last_block.header.bits

        # 2. Calcula quanto tempo levou para minerar os últimos X blocos
        actual_timespan = last_block.header.timestamp - epoch_start_block.header.timestamp
        
        target_timespan = TARGET_BLOCK_TIME * DIFFICULTY_ADJUSTMENT_INTERVAL

        # 3. Limites de segurança (Retargeting Limiting)
        # Impede que a dificuldade mude mais que 4x para cima ou para baixo de uma vez.
        # Isso evita ataques de manipulação temporal.
        if actual_timespan < target_timespan / 4:
            actual_timespan = target_timespan / 4
        if actual_timespan > target_timespan * 4:
            actual_timespan = target_timespan * 4

        # 4. Calcula o novo target
        last_target = DifficultyEngine.bits_to_target(last_block.header.bits)
        
        # A matemática básica: Novo Target = Velho Target * (Tempo Real / Tempo Ideal)
        # Se demorou muito (Tempo Real > Ideal), o Target aumenta (fica mais fácil achar hash menor).
        new_target = int(last_target * actual_timespan / target_timespan)

        # Não deixa ficar mais fácil que o Genesis (limite mínimo de dificuldade)
        max_target = DifficultyEngine.bits_to_target(GENESIS_BITS)
        if new_target > max_target:
            new_target = max_target

        return DifficultyEngine.target_to_bits(new_target)

    @staticmethod
    def bits_to_target(bits: int) -> int:
        """
        Converte o formato compacto de 32 bits para o inteirão de 256 bits (Target).
        Ex: 0x1b0404cb -> Inteiro Gigante
        """
        exponent = bits >> 24
        coefficient = bits & 0xffffff
        return coefficient * (2 ** (8 * (exponent - 3)))

    @staticmethod
    def target_to_bits(target: int) -> int:
        """
        Converte o Inteirão de volta para 32 bits compactos para salvar no Header.
        """
        bit_length = target.bit_length()
        exponent = (bit_length + 7) // 8
        coefficient = target >> (8 * (exponent - 3))

        if coefficient > 0xffffff:
            coefficient >>= 8
            exponent += 1
        
        return (exponent << 24) | coefficient

class BlockchainRules:
    """
    Classe estática e pura (Pure Logic) que valida se um bloco segue as regras.
    Não acessa banco de dados. Recebe os dados e diz Sim ou Não.
    """

    @staticmethod
    def check_pow(header: BlockHeader) -> bool:
        """
        Verifica se o hash do bloco é menor que o target declarado.
        Proof of Work: Hash(Header) <= Target
        """
        target = DifficultyEngine.bits_to_target(header.bits)
        block_hash_int = int(header.calculate_hash(), 16)
        
        return block_hash_int <= target

    @staticmethod
    def validate_block(new_block: Block, previous_block: Block) -> bool:
        """
        Valida um bloco em relação ao seu antecessor imediato.
        """
        header = new_block.header
        prev_header = previous_block.header

        # 1. Encadeamento (Chain Link)
        if header.prev_block_hash != previous_block.id:
            raise ValueError(f"Block prev_hash {header.prev_block_hash} != {previous_block.id}")

        # 2. Check PoW
        if not BlockchainRules.check_pow(header):
            raise ValueError("Proof of Work inválido: Hash acima do target")

        # 3. Validação Temporal (Time Warp Attack Protection)
        # O bloco não pode ser mais velho que a mediana dos passados (simplificado aqui para > prev)
        if header.timestamp <= prev_header.timestamp:
            raise ValueError("Timestamp inválido: Bloco no passado")

        # O bloco não pode estar muito no futuro (ex: 2 horas)
        # Isso impede que mineradores 'guardem' blocos futuros
        if header.timestamp > time.time() + 7200:
            raise ValueError("Timestamp muito no futuro")

        # 4. Validar Merkle Root Interna
        # Garante que as transações dentro do bloco batem com o header
        if not new_block.validate_merkle_root():
            raise ValueError("Merkle Root mismatch: Transações alteradas")

        return True