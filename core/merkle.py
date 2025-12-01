# core/merkle.py
import hashlib
from typing import List

class MerkleTree:
    @staticmethod
    def get_merkle_root(transaction_hashes: List[str]) -> str:
        """
        Calcula a Merkle Root de uma lista de hashes de transações.
        Seguindo o padrão Bitcoin: 
        - Double SHA-256
        - Se o número de itens for ímpar, duplica o último.
        """
        if not transaction_hashes:
            return hashlib.sha256(b'').hexdigest()

        # O processo é destrutivo para a lista, então copiamos
        current_level = transaction_hashes.copy()

        while len(current_level) > 1:
            next_level = []
            
            # Se houver número ímpar de elementos, duplica o último
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1])

            # Processa pares
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1]
                
                # Concatena e faz o hash
                # Nota: Em produção real, tratamos como bytes, aqui simplificamos com strings hex
                combined = left + right
                new_hash = MerkleTree._double_hash(combined.encode())
                next_level.append(new_hash)

            current_level = next_level

        return current_level[0]

    @staticmethod
    def _double_hash(data: bytes) -> str:
        """Bitcoin usa SHA-256(SHA-256(x))"""
        first_hash = hashlib.sha256(data).digest()
        second_hash = hashlib.sha256(first_hash).hexdigest()
        return second_hash