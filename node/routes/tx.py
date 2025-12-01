# node/routes/tx.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

from core.transaction import Transaction, TxInput, TxOutput
from node.services.mempool_service import MempoolService

router = APIRouter(prefix="/tx", tags=["Transaction"])

# --- Pydantic Models (DTOs) para validação da API ---
# Isso garante que o JSON de entrada esteja no formato correto
class TxInputDTO(BaseModel):
    prev_tx_id: Optional[str] = None
    output_index: Optional[int] = None
    public_key: Optional[str] = None
    signature: Optional[str] = None

class TxOutputDTO(BaseModel):
    amount: Optional[int] = None
    address: Optional[str] = None

class TransactionDTO(BaseModel):
    inputs: List[TxInputDTO]
    outputs: List[TxOutputDTO]
    timestamp: Optional[float] = None

# Importamos a função get_mempool do app (circular import trick ou use um container separado)
# Para simplificar aqui, vamos assumir que passamos via Depends na main
# Na prática, defina get_mempool em um arquivo node/dependencies.py

@router.post("/", status_code=201)
def submit_transaction(tx_dto: TransactionDTO, 
                       mempool: MempoolService = Depends(lambda: __import__('node.app', 
                                                                            fromlist=['get_mempool']).get_mempool())):
    """
    Endpoint para Wallet enviar uma nova transação assinada.
    """
    try:
        # 1. Converte DTO (JSON) para Objeto de Domínio (Core)
        # É chato, mas necessário para manter o Core puro sem Pydantic
        core_inputs = [
            TxInput(
                prev_tx_id=i.prev_tx_id, 
                output_index=i.output_index, 
                public_key=i.public_key, 
                signature=i.signature
            ) for i in tx_dto.inputs
        ]
        
        core_outputs = [
            TxOutput(amount=o.amount, address=o.address) for o in tx_dto.outputs
        ]
        
        # Recria a transação. O ID será recalculado automaticamente no __post_init__
        # Nota: O Timestamp deve bater com o hash assinado, então confiamos no enviado (mas validamos lógico)
        tx = Transaction(inputs=core_inputs, outputs=core_outputs)
        tx.timestamp = tx_dto.timestamp 
        
        # O calculo do hash deve bater. Se o hash gerado aqui for diferente do que foi assinado, falha.
        # (A validação de assinatura dentro do add_transaction pegará isso)

        # 2. Envia para o Service
        mempool.add_transaction(tx)
        
        return {"status": "accepted", "tx_id": tx.id}

    except ValueError as e:
        # Erros de validação (assinatura ruim, saldo insuficiente)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")