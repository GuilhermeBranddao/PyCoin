import time

import pytest

from core.block import Block
from core.transaction import Transaction, TxOutput


class TestBlock:

    @pytest.fixture
    def sample_transactions(self):
        """Cria uma lista de transações simples para teste"""
        # Criamos transações dummy. Não precisam ser válidas criptograficamente
        # para testar a estrutura do bloco, apenas precisam ter IDs diferentes.

        tx1 = Transaction(inputs=[], outputs=[TxOutput(10, "addr1")])
        # Forçamos um ID para garantir determinismo no teste, ou confiamos no hash aleatório
        # Vamos confiar no hash gerado pelo Transaction.__post_init__

        tx2 = Transaction(inputs=[], outputs=[TxOutput(20, "addr2")])
        return [tx1, tx2]

    def test_genesis_block_creation(self):
        """Testa se o bloco Gênesis segue as regras hardcoded"""
        genesis = Block.create_genesis_block()

        assert genesis.height == 0
        assert genesis.header.prev_block_hash == "0" * 64
        assert len(genesis.transactions) == 0
        assert genesis.header.bits > 0  # Deve ter alguma dificuldade definida

    def test_calculate_merkle_root(self, sample_transactions):
        """
        Testa se a Merkle Root é calculada e se altera quando as transações mudam.
        """
        # 1. Cria bloco candidato
        block = Block.create_candidate(
            transactions=sample_transactions,
            prev_hash="00" * 32,
            block_height=1,
            bits=0x1d00ffff
        )

        original_root = block.header.merkle_root
        assert len(original_root) == 64
        assert block.validate_merkle_root() is True

        # 2. Modifica uma transação na lista (Simula ataque ou corrupção)
        # Vamos alterar o ID da primeira transação 'na marra' ou trocar a ordem
        block.transactions.reverse()

        # Como a ordem mudou, a Merkle Root calculada agora deve ser diferente da que está no Header
        assert block.validate_merkle_root() is False

    def test_block_serialization_and_hash(self, sample_transactions):
        """
        Testa se a serialização para mineração é consistente (Little Endian, formatos).
        """
        block = Block.create_candidate(
            transactions=sample_transactions,
            prev_hash="ab" * 32,
            block_height=5,
            bits=0x1d00ffff
        )

        # O Hash deve ser determinístico
        hash1 = block.id
        hash2 = block.id
        assert hash1 == hash2

        # Verifica se header.nonce afeta o hash
        block.header.nonce = 12345
        hash3 = block.id
        assert hash1 != hash3

    def test_create_candidate_sets_correct_metadata(self):
        """Testa se create_candidate preenche os campos corretamente"""
        txs = []
        prev_hash = "aa" * 32
        bits = 12345

        block = Block.create_candidate(txs, prev_hash, block_height=10, bits=bits)

        assert block.header.prev_block_hash == prev_hash
        assert block.header.bits == bits
        assert block.header.nonce == 0
        assert block.height == 10
        # Timestamp deve ser recente (delta de 1 segundo)
        assert abs(block.header.timestamp - time.time()) < 5
