import pytest
from unittest.mock import MagicMock
from node.services.mempool_service import MempoolService
from node.storage.chain_repository import ChainRepository
from core.transaction import Transaction, TxInput, TxOutput

@pytest.fixture
def mock_repo():
    repo = MagicMock(spec=ChainRepository)
    # Configura um UTXO padrão que existe
    repo.get_utxo.return_value = {'amount': 100, 'address': 'alice'}
    return repo

@pytest.fixture
def mempool(mock_repo):
    return MempoolService(chain_repository=mock_repo)

@pytest.fixture
def basic_tx():
    """Cria uma TX válida simulada"""
    inp = TxInput(prev_tx_id="tx_old", output_index=0)
    out = TxOutput(amount=50, address="bob")
    tx = Transaction(inputs=[inp], outputs=[out])
    # Mock da validação criptográfica para focar na lógica da mempool
    tx.is_valid = MagicMock(return_value=True) 
    return tx

class TestMempoolService:
    
    def test_add_transaction_success(self, mempool, basic_tx):
        """Testa o caminho feliz"""
        result = mempool.add_transaction(basic_tx)
        
        assert result is True
        assert basic_tx.id in mempool._pending_txs
        # Verifica se o input foi travado no cache
        assert "tx_old:0" in mempool._spent_inputs_cache

    def test_add_transaction_duplicate_ignored(self, mempool, basic_tx):
        """Se enviar a mesma TX 2x, deve retornar True mas não adicionar de novo"""
        mempool.add_transaction(basic_tx)
        result = mempool.add_transaction(basic_tx) # Segunda vez
        
        assert result is True
        assert len(mempool._pending_txs) == 1

    def test_add_transaction_invalid_signature(self, mempool, basic_tx):
        """Se a assinatura (stateless) falhar"""
        basic_tx.is_valid.return_value = False
        
        with pytest.raises(ValueError, match="assinatura inválida"):
            mempool.add_transaction(basic_tx)

    def test_add_transaction_missing_utxo(self, mempool, basic_tx, mock_repo):
        """Se tentar gastar dinheiro que não existe no DB"""
        mock_repo.get_utxo.return_value = None # UTXO não encontrado
        
        with pytest.raises(ValueError, match="não existe ou já foi gasto"):
            mempool.add_transaction(basic_tx)

    def test_double_spend_in_mempool(self, mempool, basic_tx):
        """
        Cenário: Alice manda Tx1 gastando Input A.
        Alice tenta mandar Tx2 também gastando Input A.
        A mempool deve barrar a Tx2.
        """
        # 1. Adiciona a primeira
        mempool.add_transaction(basic_tx)
        
        # 2. Cria Tx2 gastando o MESMO input
        tx2 = Transaction(inputs=[basic_tx.inputs[0]], outputs=[TxOutput(50, "evil")])
        tx2.is_valid = MagicMock(return_value=True)
        # Força IDs diferentes
        tx2.id = "tx_different_hash" 

        # 3. Tenta adicionar
        with pytest.raises(ValueError, match="Double Spend na Mempool"):
            mempool.add_transaction(tx2)

    def test_remove_transactions_cleans_cache(self, mempool, basic_tx):
        """Testa se a mempool libera os inputs quando o bloco é minerado"""
        mempool.add_transaction(basic_tx)
        assert "tx_old:0" in mempool._spent_inputs_cache
        
        # Simula bloco chegando
        mempool.remove_transactions([basic_tx])
        
        assert basic_tx.id not in mempool._pending_txs
        assert "tx_old:0" not in mempool._spent_inputs_cache