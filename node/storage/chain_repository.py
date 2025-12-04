# node/storage/chain_repository.py
import json
import os
import struct
from typing import List, Optional

import plyvel  # LevelDB wrapper

from core.block import Block, BlockHeader
from core.transaction import Transaction


class ChainRepository:
    def __init__(self, db_path: str = "./data/chainstate",
                 blocks_path: str = "./data/blocks"):
        self.blocks_dir = blocks_path
        self.current_block_file = "blk00000.dat"

        # Cria diretórios se não existirem
        os.makedirs(db_path, exist_ok=True)
        os.makedirs(blocks_path, exist_ok=True)

        # Inicializa LevelDB
        # create_if_missing=True cria o DB se não existir
        self.db = plyvel.DB(db_path, create_if_missing=True)

    def close(self):
        self.db.close()

    # --- BLOCK STORAGE (Hybrid: File + Index) ---

    def save_block(self, block: Block):
        """
        1. Escreve os dados brutos no blocks.dat
        2. Atualiza o índice no LevelDB
        3. Atualiza o UTXO Set
        """
        # Serializa bloco para JSON bytes (ou binário puro se preferir)
        block_data = json.dumps(block.to_dict()).encode()
        block_hash = block.id

        # 1. Append no arquivo flat
        file_path = os.path.join(self.blocks_dir, self.current_block_file)

        with open(file_path, "ab") as f:
            offset = f.tell()  # Pega a posição atual antes de escrever
            f.write(struct.pack("<I", len(block_data)))  # Header de tamanho (4 bytes)
            f.write(block_data)
            length = len(block_data)

        # 2. Batch Write no LevelDB (Atomicidade)
        # Usamos batch para garantir que ou salva tudo ou nada
        with self.db.write_batch() as wb:
            # A. Salva Índice do Bloco: Prefix 'b' + Hash
            # Value: File, Offset, Length
            location_info = f"{self.current_block_file}|{offset}|{length}".encode()
            wb.put(b'b-' + block_hash.encode(), location_info)

            # B. Atualiza 'Last Hash' (Tip da chain)
            wb.put(b'H-last_block', block_hash.encode())

            # C. Atualiza UTXO Set (A parte mais importante!)
            self._update_utxo_set(wb, block)

    def get_block(self, block_hash: str) -> Optional[Block]:
        """Recupera bloco usando o índice do LevelDB para ler o arquivo"""
        location_bytes = self.db.get(b'b-' + block_hash.encode())
        if not location_bytes:
            return None

        file_name, offset, length = location_bytes.decode().split('|')
        offset = int(offset)
        length = int(length)

        file_path = os.path.join(self.blocks_dir, file_name)

        with open(file_path, "rb") as f:
            f.seek(offset + 4)  # Pula os 4 bytes de tamanho
            block_data = f.read(length)

        block_dict = json.loads(block_data)

        # 1. Reconstrói as Transações
        tx_objects = []
        for tx_data in block_dict['transactions']:
            tx_objects.append(Transaction.from_dict(tx_data))

        # 2. Reconstrói o Header
        header_obj = BlockHeader(**block_dict['header'])

        # 3. Retorna o Objeto Block completo
        return Block(
            header=header_obj,
            transactions=tx_objects,
            height=block_dict['height']
        )

    def get_last_block_hash(self) -> Optional[str]:
        val = self.db.get(b'H-last_block')
        return val.decode() if val else None

    # --- UTXO MANAGEMENT ---

    def _update_utxo_set(self, batch, block: Block):
        """
        Remove inputs gastos e adiciona novos outputs.
        Executado dentro do batch do save_block.
        """
        # 1. Gastar Inputs (Remover do DB)
        for tx in block.transactions:
            if not tx.inputs: continue  # Coinbase pode não ter inputs normais

            for inp in tx.inputs:
                if inp.prev_tx_id == "00000000": continue  # Ignora input de coinbase

                # Remove UTXO: Key u-{txid}-{index}
                utxo_key = f"u-{inp.prev_tx_id}-{inp.output_index}".encode()
                batch.delete(utxo_key)

        # 2. Criar Outputs (Adicionar ao DB)
        for tx in block.transactions:
            for idx, output in enumerate(tx.outputs):
                utxo_key = f"u-{tx.id}-{idx}".encode()

                # Value: Serializa o UTXO (Amount, Address/Script)
                # Otimização: Salvar binário com struct
                utxo_val = json.dumps({
                    "amount": output.amount,
                    "address": output.address
                }).encode()

                batch.put(utxo_key, utxo_val)

    def get_utxo(self, tx_id: str, index: int) -> Optional[dict]:
        """Consulta rápida para validação"""
        key = f"u-{tx_id}-{index}".encode()
        data = self.db.get(key)
        if not data:
            return None
        return json.loads(data)

    def get_utxos_by_address(self, address: str) -> List[dict]:
        """
        Itera sobre todos os UTXOs ativos e filtra pelo endereço.
        Retorna lista de {tx_id, output_index, amount}.
        """

        # TODO: Em produção, teríamos um índice secundário (tabela de endereços). Para agora, faremos um scan nos UTXOs, que é aceitável para MVP.
        utxos = []
        # Itera apenas sobre chaves que começam com 'u-'
        for key, value in self.db.iterator(prefix=b'u-'):
            data = json.loads(value)
            if data['address'] == address:
                # A chave é b'u-{txid}-{index}'
                # Decodificamos para pegar os IDs
                parts = key.decode().split('-')
                tx_id = parts[1]
                output_index = int(parts[2])

                utxos.append({
                    "tx_id": tx_id,
                    "output_index": output_index,
                    "amount": data['amount']
                })
        return utxos
