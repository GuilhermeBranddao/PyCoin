# core/block.py
import hashlib
import struct
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List

from config import GENESIS_BITS
from core.merkle import MerkleTree
from core.transaction import Transaction


@dataclass
class BlockHeader:
    """
    O Cabeçalho é a única coisa que precisa ser minerada (PoW).
    Contém os metadados cruciais para a imutabilidade.
    """
    version: int
    prev_block_hash: str
    merkle_root: str
    timestamp: int
    bits: int  # Representação compacta do Target (Dificuldade)
    nonce: int = 0

    def serialize_for_mining(self) -> bytes:
        """
        Serializa os dados em formato binário compacto para o minerador (Little-endian).
        Formato: Version(4B) + PrevHash(32B) + Merkle(32B) + Time(4B) + Bits(4B) + Nonce(4B)
        """
        try:
            prev_hash_bytes = bytes.fromhex(self.prev_block_hash)
            merkle_bytes = bytes.fromhex(self.merkle_root)
        except ValueError:
            # Fallback para genesis ou hashes inválidos durante testes
            prev_hash_bytes = b'\x00' * 32
            merkle_bytes = b'\x00' * 32

        return struct.pack(
            '<I32s32sIII',
            self.version,
            prev_hash_bytes,
            merkle_bytes,
            self.timestamp,
            self.bits,
            self.nonce
        )

    def calculate_hash(self) -> str:
        """Gera o ID do bloco (Double SHA-256 do header serializado)"""
        header_bin = self.serialize_for_mining()
        hash1 = hashlib.sha256(header_bin).digest()
        hash2 = hashlib.sha256(hash1).digest()
        # Invertemos os bytes ([::-1]) antes de converter para Hex.
        # Isso alinha o Node com a lógica de 'Big Endian' do Minerador.
        return hash2[::-1].hex()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Block:
    """
    O Bloco completo. Une o Cabeçalho com o Corpo (Transações).
    """
    header: BlockHeader
    transactions: List[Transaction]

    # Propriedades auxiliares
    height: int = 0  # Altura do bloco na chain (não faz parte do hash, é metadado local)

    @property
    def id(self) -> str:
        return self.header.calculate_hash()

    def validate_merkle_root(self) -> bool:
        """
        Verifica se as transações dentro deste bloco batem com a Merkle Root do cabeçalho.
        Isso impede que um node malicioso altere uma transação dentro de um bloco válido.
        """
        tx_hashes = [tx.id for tx in self.transactions]
        calculated_root = MerkleTree.get_merkle_root(tx_hashes)
        return calculated_root == self.header.merkle_root

    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header.to_dict(),
            "transactions": [tx.to_dict() for tx in self.transactions],
            "hash": self.id,
            "height": self.height
        }

    @classmethod
    def create_candidate(cls,
                         transactions: List[Transaction],
                         prev_hash: str,
                         block_height: int,
                         bits: int,
                         version: int = 1):
        """
        Cria um bloco 'candidato' para ser minerado.
        O Nonce começa em 0.

        Calculamos a raiz antes de criar o header. Isso "congela" a lista de transações. 
        Se alguém tentar adicionar uma transação depois, a raiz muda e o hash do bloco (PoW) 
        torna-se inválido.
        """
        # 1. Calcula a Merkle Root das transações fornecidas
        tx_hashes = [tx.id for tx in transactions]
        merkle_root = MerkleTree.get_merkle_root(tx_hashes)

        # 2. Cria o Header
        header = BlockHeader(
            version=version,
            prev_block_hash=prev_hash,
            merkle_root=merkle_root,
            timestamp=int(time.time()),
            bits=bits,
            nonce=0
        )

        # 3. Retorna o objeto Bloco (ainda inválido pois não tem PoW feito)
        return cls(header=header, transactions=transactions, height=block_height)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Block":
        header_data = data["header"]

        header = BlockHeader(
            version=header_data["version"],
            prev_block_hash=header_data["prev_block_hash"],
            merkle_root=header_data["merkle_root"],
            timestamp=header_data["timestamp"],
            bits=header_data["bits"],
            nonce=header_data["nonce"]
        )

        transactions = [
            Transaction.from_dict(tx) for tx in data["transactions"]
        ]

        return cls(
            header=header,
            transactions=transactions,
            height=data.get("height", 0)
        )

    @staticmethod
    def create_genesis_block() -> 'Block':
        """Cria o bloco Gênesis hardcoded."""
        # Transação Gênesis (Hardcoded)
        # Em um sistema real, seria uma transação especial sem inputs
        genesis_tx_data = "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks"

        # Como não temos uma TX válida ainda, vamos simular o hash para o merkle
        merkle_root = hashlib.sha256(genesis_tx_data.encode()).hexdigest()

        header = BlockHeader(
            version=1,
            prev_block_hash="0" * 64,
            merkle_root=merkle_root,
            timestamp=1700000000,  # Data fixa
            bits=GENESIS_BITS,    # Dificuldade mínima
            nonce=2083236         # Nonce que satisfaz a dificuldade acima (exemplo)
        )

        return Block(header=header, transactions=[], height=0)
