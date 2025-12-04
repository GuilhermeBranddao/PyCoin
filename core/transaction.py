import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from typing import List

from cryptography.exceptions import InvalidSignature

# Utilizaremos as mesmas libs de criptografia que você já estava usando
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import ec


@dataclass
class TxOutput:
    """
    Representa um valor trancado (Lock).
    No Bitcoin, isso é o 'ScriptPubKey'.
    """
    amount: int
    address: str  # O endereço que "possui" este valor (Hash da chave pública)

    def to_dict(self):
        return asdict(self)


@dataclass
class TxInput:
    """
    Representa o uso de um valor anterior (Unlock).
    Aponta para um TxOutput passado.
    """
    prev_tx_id: str      # Hash da transação onde o dinheiro está
    output_index: int    # Qual índice da lista de outputs daquela transação
    public_key: str = ""  # Chave pública para validar a assinatura (Hex)
    signature: str = ""  # A prova criptográfica (Hex)

    def to_dict(self):
        return asdict(self)


@dataclass
class Transaction:
    inputs: List[TxInput]
    outputs: List[TxOutput]
    timestamp: float = field(default_factory=time.time)
    id: str = field(init=False)  # O Hash da transação (TxID)

    def __post_init__(self):
        # Calcula o ID assim que a transação é criada
        self.id = self.calculate_hash()

    def to_dict(self):
        """Serializa a transação para dicionário (útil para JSON/API)"""
        return {
            "inputs": [i.to_dict() for i in self.inputs],
            "outputs": [o.to_dict() for o in self.outputs],
            "timestamp": self.timestamp
        }

    @staticmethod
    def from_dict(data: dict) -> "Transaction":
        """
        Reconstrói uma Transaction a partir de um dicionário.
        """
        # Reconstruir inputs
        inputs = [
            TxInput(
                prev_tx_id=i["prev_tx_id"],
                output_index=i["output_index"],
                public_key=i["public_key"],
                signature=i.get("signature"),
                # pubkey=i.get("pubkey")
            )
            for i in data["inputs"]
        ]

        # Reconstruir outputs
        outputs = [
            TxOutput(
                amount=o["amount"],
                address=o["address"]
            )
            for o in data["outputs"]
        ]

        # Criar objeto Transaction SEM chamar __post_init__ automaticamente
        tx = Transaction(inputs=inputs, outputs=outputs, timestamp=data["timestamp"])

        # ⚠️ IMPORTANTE:
        # Ao reconstruir a transação, o ID deve ser exatamente o armazenado.
        # Então definimos manualmente:
        tx.id = data.get("id", tx.calculate_hash())

        return tx

    def calculate_hash(self) -> str:
        """
        Gera o hash da transação. 
        IMPORTANTE: Para o TxID, nós NÃO incluímos as assinaturas dos inputs.
        Isso resolve a maleabilidade de transação (SegWit resolveu isso no BTC, 
        mas aqui simplificamos ignorando a assinatura no hash do ID).
        """
        # Cria uma cópia dos inputs sem a assinatura para o hash estável
        clean_inputs = []
        for inp in self.inputs:
            clean_inputs.append({
                "prev_tx_id": inp.prev_tx_id,
                "output_index": inp.output_index,
                # Não incluímos signature/pubkey no ID da transação
            })

        tx_content = {
            "inputs": clean_inputs,
            "outputs": [o.to_dict() for o in self.outputs],
            "timestamp": self.timestamp
        }

        # sort_keys=True é OBRIGATÓRIO para garantir determinismo
        tx_string = json.dumps(tx_content, sort_keys=True).encode()
        return hashlib.sha256(tx_string).hexdigest()

    def sign_input(self, input_index: int, private_key: ec.EllipticCurvePrivateKey):
        """
        Assina um input específico.
        Você assina o hash da transação inteira para garantir que 
        ninguém mude os outputs (destino do dinheiro).

        "Isso impede que alguém pegue sua assinatura válida de um pagamento de 10 moedas 
        para o João e a coloque em uma transação pagando 10 moedas para o Hacker. 
        Se os outputs mudarem, o hash muda, e a assinatura torna-se inválida."
        """
        if input_index >= len(self.inputs):
            raise ValueError("Índice de input inexistente")

        # 1. O que vamos assinar? O Hash da transação atual.
        # Isso garante que "Eu autorizo gastar o input X para criar ESTES outputs Y"
        message_to_sign = self.calculate_hash().encode()

        # 2. Assinar com a chave privada
        signature = private_key.sign(
            message_to_sign,
            ec.ECDSA(hashes.SHA256())
        )

        # 3. Guardar a assinatura e a chave pública (em hex) no Input
        public_key = private_key.public_key()
        pub_bytes = public_key.public_bytes(
            encoding=crypto_serialization.Encoding.PEM,
            format=crypto_serialization.PublicFormat.SubjectPublicKeyInfo
        )

        self.inputs[input_index].signature = signature.hex()
        # Armazenamos a pubkey limpa para facilitar verificação
        self.inputs[input_index].public_key = pub_bytes.hex()

    def is_valid(self) -> bool:
        """
        Verificação MATEMÁTICA da transação (Stateless).
        O core não verifica saldo (Stateful), apenas se as assinaturas batem.

        "A pessoa que criou este input possui a chave privada correspondente à chave pública informada?"
        """
        # 1. Verifica hash
        if self.id != self.calculate_hash():
            return False

        # 2. Valida assinaturas de todos os inputs
        message_to_verify = self.calculate_hash().encode()

        for inp in self.inputs:
            # Transações Coinbase (recompensa) não têm assinatura normal
            if inp.prev_tx_id == "00000000":
                continue

            if not inp.signature or not inp.public_key:
                return False

            try:
                # Reconstrói a chave pública
                public_key_bytes = bytes.fromhex(inp.public_key)
                public_key = crypto_serialization.load_pem_public_key(public_key_bytes)

                # Verifica a assinatura
                signature_bytes = bytes.fromhex(inp.signature)
                public_key.verify(
                    signature_bytes,
                    message_to_verify,
                    ec.ECDSA(hashes.SHA256())
                )
            except (InvalidSignature, ValueError):
                return False

        return True

    @classmethod
    def create_coinbase(cls, receiver_address: str, block_height: int, reward: int = 50):
        """
        Cria a transação de recompensa do minerador.
        Não tem input real (surge do nada, prev_tx_id é zerado).

        É a única transação que cria dinheiro do nada
        """
        # Input dummy. No Bitcoin, colocamos o "Block Height" aqui para garantir unicidade
        coinbase_input = TxInput(
            prev_tx_id="00000000",
            output_index=block_height,  # Garante que o hash mude a cada bloco
            signature="coinbase",
            public_key=""
        )

        tx_output = TxOutput(amount=reward, address=receiver_address)

        return cls(inputs=[coinbase_input], outputs=[tx_output])
