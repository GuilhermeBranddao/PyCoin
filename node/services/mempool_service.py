# node/services/mempool_service.py
from typing import List, Dict, Set
from core.transaction import Transaction
from node.storage.chain_repository import ChainRepository

class MempoolService:
    def __init__(self, chain_repository: ChainRepository):
        # Usamos um Dict para acesso O(1) pelo TxID
        self._pending_txs: Dict[str, Transaction] = {}
        # Set auxiliar para garantir que não gastamos o mesmo input 2x na mempool
        # Formato: "txid_prev:index"
        self._spent_inputs_cache: Set[str] = set()
        self.repository = chain_repository

    def add_transaction(self, tx: Transaction) -> bool:
        """
        Recebe uma transação, valida e adiciona à fila.
        Retorna True se aceita, False (ou raise) se rejeitada.
        """
        # 1. Já conhecemos essa TX?
        if tx.id in self._pending_txs:
            return True # Já está lá, ignorar

        # 2. Validação Stateless (Assinaturas e Formato) - CORE
        if not tx.is_valid():
            raise ValueError(f"Transação {tx.id} tem assinatura inválida ou formato incorreto.")

        # 3. Validação Stateful (Saldo e Double Spend) - STORAGE
        # Precisamos verificar se os inputs referenciados:
        # a) Existem no UTXO set (são dinheiro real)
        # b) Não foram gastos por outra TX já na mempool
        
        for inp in tx.inputs:
            # Check A: Existe no banco de dados?
            utxo = self.repository.get_utxo(inp.prev_tx_id, inp.output_index)
            if not utxo:
                raise ValueError(f"Input {inp.prev_tx_id}:{inp.output_index} não existe ou já foi gasto.")

            # Check B: Já foi usado na mempool?
            input_key = f"{inp.prev_tx_id}:{inp.output_index}"
            if input_key in self._spent_inputs_cache:
                raise ValueError(f"Double Spend na Mempool: Input {input_key} já sendo usado.")

        # 4. Adiciona à Mempool
        self._pending_txs[tx.id] = tx
        
        # Marca inputs como "temporariamente gastos"
        for inp in tx.inputs:
            input_key = f"{inp.prev_tx_id}:{inp.output_index}"
            self._spent_inputs_cache.add(input_key)

        print(f"Mempool: Transação {tx.id} aceita.")
        return True

    def get_candidate_transactions(self, limit: int = 2000) -> List[Transaction]:
        """
        O Minerador chama isso para montar o bloco.
        Pode implementar lógica de prioridade por Fee aqui no futuro.
        """
        return list(self._pending_txs.values())[:limit]

    def remove_transactions(self, txs: List[Transaction]):
        """
        Chamado quando um bloco novo chega. 
        Devemos remover da mempool todas as transações que entraram no bloco.
        """
        for tx in txs:
            if tx.id in self._pending_txs:
                del self._pending_txs[tx.id]
                
                # Libera o cache de inputs (embora agora estejam gastos na chain, 
                # removemos da cache da mempool para manter limpo)
                for inp in tx.inputs:
                    input_key = f"{inp.prev_tx_id}:{inp.output_index}"
                    if input_key in self._spent_inputs_cache:
                        self._spent_inputs_cache.remove(input_key)