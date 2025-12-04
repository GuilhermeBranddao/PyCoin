import pytest
import os
import json
from core.block import Block
from core.transaction import Transaction, TxInput, TxOutput
from node.storage.chain_repository import ChainRepository

@pytest.fixture
def repo(tmp_path):
    """
    Cria um repo apontando para uma pasta temporária isolada.
    """
    db_path = tmp_path / "chainstate"
    blocks_path = tmp_path / "blocks"
    repository = ChainRepository(db_path=str(db_path), blocks_path=str(blocks_path))
    yield repository
    repository.close()

class TestChainRepository:
    
    def test_save_and_get_genesis_block(self, repo):
        genesis = Block.create_genesis_block()
        
        # 1. Salvar
        repo.save_block(genesis)
        
        # 2. Recuperar
        loaded_block = repo.get_block(genesis.id)
        
        assert loaded_block is not None
        assert loaded_block.id == genesis.id
        assert loaded_block.header.timestamp == genesis.header.timestamp
        assert repo.get_last_block_hash() == genesis.id

    def test_utxo_update_logic(self, repo):
        """
        Testa o ciclo de vida do dinheiro:
        Bloco 1 (Coinbase) -> Cria UTXO
        Bloco 2 (Gasto) -> Remove UTXO antigo, Cria novos
        """
        # --- Passo 1: Bloco Gênesis (Coinbase para Alice) ---
        genesis = Block.create_genesis_block()
        # Hack: Vamos injetar uma coinbase manual no genesis para facilitar
        tx_coinbase = Transaction.create_coinbase("alice_addr", 1, 50)
        genesis.transactions = [tx_coinbase]
        # Recalcula hash/merkle simulado se necessário, mas para storage basta salvar
        repo.save_block(genesis)

        # Verifica se UTXO da Alice foi criado
        utxos = repo.get_utxos_by_address("alice_addr")
        assert len(utxos) == 1
        assert utxos[0]['amount'] == 50

        # --- Passo 2: Bloco 2 (Alice paga Bob) ---
        # Input: UTXO anterior
        inp = TxInput(prev_tx_id=tx_coinbase.id, output_index=0)
        # Output: 30 pra Bob, 20 troco pra Alice
        out1 = TxOutput(30, "bob_addr")
        out2 = TxOutput(20, "alice_addr")
        
        tx_spend = Transaction(inputs=[inp], outputs=[out1, out2])
        
        block2 = Block.create_candidate([tx_spend], genesis.id, 2, 0)
        repo.save_block(block2)

        # Verificações Finais
        
        # 1. UTXO original da Alice deve ter sumido
        old_utxo = repo.get_utxo(tx_coinbase.id, 0)
        assert old_utxo is None
        
        # 2. Bob deve ter 30
        bob_utxos = repo.get_utxos_by_address("bob_addr")
        assert len(bob_utxos) == 1
        assert bob_utxos[0]['amount'] == 30
        
        # 3. Alice deve ter 20 (novo UTXO)
        alice_utxos = repo.get_utxos_by_address("alice_addr")
        assert len(alice_utxos) == 1
        assert alice_utxos[0]['amount'] == 20
        assert alice_utxos[0]['tx_id'] == tx_spend.id