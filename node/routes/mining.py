# node/routes/mining.py
import time
import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from core.block import Block, BlockHeader
from core.blockchain import DifficultyEngine
from node.services.mempool_service import MempoolService
from node.storage.chain_repository import ChainRepository

# Dependências (idealmente viriam de node/dependencies.py)
from node.app import get_mempool, get_chain_repo

router = APIRouter(prefix="/mining", tags=["Mining"])

# Cache simples em memória para guardar os Jobs enviados aos mineradores
# JobID -> {header_parcial, transacoes}
mining_jobs = {}

class MiningWorkResponse(BaseModel):
    job_id: Optional[str] = None
    version: Optional[int] = None
    prev_hash: Optional[str] = None
    merkle_root: Optional[str] = None
    timestamp: Optional[int] = None
    bits: Optional[int] = None
    target: Optional[str] = None # Enviamos o target como string hexa para facilitar pro miner

class SubmitWorkRequest(BaseModel):
    job_id: Optional[str] = None
    nonce: Optional[int] = None
    timestamp: Optional[int] = None

@router.get("/get_work", response_model=MiningWorkResponse)
def get_work(
    mempool: MempoolService = Depends(get_mempool),
    repo: ChainRepository = Depends(get_chain_repo)
):
    """
    Minerador pede trabalho. O Node constrói o candidato.
    """
    # 1. Pegar último bloco (Para saber prev_hash e calcular diff)
    last_block_hash = repo.get_last_block_hash()
    
    # Se for o primeiro boot e não tiver nada, cria Genesis virtual ou falha
    if not last_block_hash:
        # Em produção, você carregaria o Genesis do arquivo de config
        raise HTTPException(status_code=503, detail="Node syncing or initializing")
        
    last_block = repo.get_block(last_block_hash)
    
    # 2. Selecionar transações da Mempool
    transactions = mempool.get_candidate_transactions()
    
    # IMPORTANTE: Adicionar Coinbase (Recompensa)
    # Por enquanto, mandamos para um endereço padrão ou o minerador manda o endereço dele no request
    # Vamos simplificar: O Node define quem ganha (ex: carteira do dono do node) ou 
    # Melhor: O Minerador manda o endereço dele como parametro na URL? 
    # Padrão Stratum: O Minerador constrói a Coinbase. Padrão GetBlockTemplate: O Node constrói.
    # Vamos usar o padrão Node Constrói para simplificar.
    
    # 3. Construir Candidato
    # TODO: Calcular 'bits' real usando DifficultyEngine
    bits = last_block.header.bits 
    
    candidate = Block.create_candidate(
        transactions=transactions,
        prev_hash=last_block.id,
        block_height=last_block.height + 1,
        bits=bits
    )
    
    # 4. Salvar Job
    job_id = uuid.uuid4().hex
    mining_jobs[job_id] = candidate # Guardamos o bloco inteiro na memória
    
    return MiningWorkResponse(
        job_id=job_id,
        version=candidate.header.version,
        prev_hash=candidate.header.prev_block_hash,
        merkle_root=candidate.header.merkle_root,
        timestamp=candidate.header.timestamp,
        bits=candidate.header.bits,
        target=hex(DifficultyEngine.bits_to_target(candidate.header.bits))
    )

@router.post("/submit_work")
def submit_work(
    submission: SubmitWorkRequest,
    repo: ChainRepository = Depends(get_chain_repo),
    mempool: MempoolService = Depends(get_mempool)
):
    """
    Minerador achou o Nonce!
    """
    if submission.job_id not in mining_jobs:
        raise HTTPException(status_code=400, detail="Job not found or expired")
        
    candidate_block = mining_jobs[submission.job_id]
    
    # 1. Atualiza o header com o que o minerador achou
    header = candidate_block.header
    header.nonce = submission.nonce
    header.timestamp = submission.timestamp # O minerador pode ter atualizado o tempo
    
    # 2. Validação Rápida (PoW)
    # O Node verifica se o trabalho é válido antes de propagar
    # Importante: Usar a classe BlockchainRules que criamos no Core
    from core.blockchain import BlockchainRules
    
    if not BlockchainRules.check_pow(header):
        raise HTTPException(status_code=400, detail="Invalid Proof of Work")
        
    # 3. Salvar Bloco!
    print(f"💰 Bloco Minerado! Height: {candidate_block.height}, Hash: {candidate_block.id}")
    repo.save_block(candidate_block)
    
    # 4. Limpar Mempool
    mempool.remove_transactions(candidate_block.transactions)
    
    # 5. Limpar Jobs antigos (Opcional, ou deixa expirar)
    mining_jobs.clear() 
    
    return {"status": "success", "block_hash": candidate_block.id}