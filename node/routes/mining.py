# node/routes/mining.py
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from config import BLOCK_REWARD, DIFFICULTY_ADJUSTMENT_INTERVAL
from core.block import Block
from core.blockchain import DifficultyEngine
from core.transaction import Transaction
from node.dependencies import get_chain_repo, get_mempool
from node.services.mempool_service import MempoolService
from node.storage.chain_repository import ChainRepository

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
    target: Optional[str] = None  # Enviamos o target como string hexa para facilitar pro miner


class SubmitWorkRequest(BaseModel):
    job_id: Optional[str] = None
    nonce: Optional[int] = None
    timestamp: Optional[int] = None


def calculate_fees(transactions: list[Transaction],
                   repo: ChainRepository) -> int:
    """
    Calcula a taxa total do bloco.
    Fee = Soma(Inputs) - Soma(Outputs)
    """
    total_fees = 0

    for tx in transactions:
        # Calcular valor total dos inputs (precisamos olhar no banco)
        input_amount = 0
        for inp in tx.inputs:
            utxo = repo.get_utxo(inp.prev_tx_id, inp.output_index)
            if utxo:
                input_amount += utxo['amount']
            else:
                # Se não achou UTXO, é perigoso, mas a validação do bloco pegaria.
                # Aqui assumimos validade pois veio da mempool.
                pass

        # Calcular valor total dos outputs
        output_amount = sum(o.amount for o in tx.outputs)

        # A diferença é a gorjeta do minerador
        fee = input_amount - output_amount
        total_fees += fee

    return total_fees


@router.get("/get_work", response_model=MiningWorkResponse)
def get_work(
    miner_address: str = Query(..., description="Endereço da carteira para receber a recompensa"),
    mempool: MempoolService = Depends(get_mempool),
    repo: ChainRepository = Depends(get_chain_repo)
):
    """
    Gera um bloco candidato contendo a transação de pagamento para o minerador. (Protocolo GetBlockTemplate simplificado).
    Responsável por calcular a dificuldade correta para o próximo bloco.
    """

    # -----------------------------------------------------------
    # 1. Recuperação do Estado Atual (Head da Chain)
    # -----------------------------------------------------------
    last_block_hash = repo.get_last_block_hash()

    if not last_block_hash:
        # Em produção, o Node deve carregar o Genesis automaticamente no boot.
        raise HTTPException(status_code=503, detail="Node syncing or initializing")

    # Carrega do DB (retorna dict) e converte para Objeto de Domínio
    last_block = repo.get_block(last_block_hash)
    # last_block = Block.from_dict(last_block_data)

    # -----------------------------------------------------------
    # 2. Seleção de Transações (Mempool)
    # -----------------------------------------------------------
    transactions = mempool.get_candidate_transactions()

    # 2. Calcular Taxas (Fees)
    # Somamos todas as taxas das transações selecionadas
    fees = calculate_fees(transactions, repo)
    total_reward = BLOCK_REWARD + fees

    # 3. Criar a Transação Coinbase (Pagamento do Minerador)
    # Ela DEVE ser a primeira transação da lista
    next_height = last_block.height + 1
    coinbase_tx = Transaction.create_coinbase(
        receiver_address=miner_address,
        block_height=next_height,
        reward=total_reward
    )

    # Lista final: [Coinbase, Tx1, Tx2, ...]
    block_transactions = [coinbase_tx] + transactions

    # NOTA: A Transação Coinbase (Recompensa) deve ser inserida aqui ou
    # pelo minerador. Nesta arquitetura, assumimos que o Miner a insere,
    # ou o Node insere uma padrão para a wallet do sistema.

    # -----------------------------------------------------------
    # 3. Cálculo da Dificuldade (Consensus Rules)
    # -----------------------------------------------------------
    bits = last_block.header.bits

    # TODO: Integar a Engine full

    # Verifica se fechamos uma Época (Ciclo de Ajuste)
    if next_height % DIFFICULTY_ADJUSTMENT_INTERVAL == 0:
        print(f"⚖️  Fim de Época detectado no bloco {last_block.height}. Calculando nova dificuldade...")

        # Precisamos achar o bloco onde este ciclo começou
        # Ex: Se intervalo é 10, e estamos no 20, o ciclo começou no 10.
        # Andamos para trás na chain (Backtracking).
        # TODO: Em produção, você teria um índice por altura no DB.

        epoch_start_block = last_block

        # Segurança: Loop para voltar X blocos
        for i in range(DIFFICULTY_ADJUSTMENT_INTERVAL - 1):
            prev_hash = epoch_start_block.header.prev_block_hash

            # Se chegarmos no Genesis antes da hora (early chain), paramos
            if prev_hash == ("0" * 64) or not prev_hash:
                break

            block_data = repo.get_block(prev_hash)
            if not block_data:
                print(f"⚠️ Erro de integridade: Bloco {prev_hash} não encontrado.")
                break

            # epoch_start_block = Block.from_dict(block_data)

        # O Core (DifficultyEngine) faz a matemática pura
        bits = DifficultyEngine.calculate_next_work_required(
            last_block=last_block,
            epoch_start_block=epoch_start_block
        )

        new_target_hex = hex(DifficultyEngine.bits_to_target(bits))
        print(f"📉 Dificuldade Ajustada! Novo Target: {new_target_hex[:10]}...")

    # -----------------------------------------------------------
    # 4. Construção do Candidato e Cache
    # -----------------------------------------------------------
    candidate = Block.create_candidate(
        transactions=block_transactions,
        prev_hash=last_block.id,
        block_height=last_block.height + 1,
        bits=bits
    )

    # Salvamos em memória para validar o Nonce quando o minerador retornar
    job_id = uuid.uuid4().hex
    mining_jobs[job_id] = candidate

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
    header.timestamp = submission.timestamp  # O minerador pode ter atualizado o tempo

    # 2. Validação Rápida (PoW)
    # O Node verifica se o trabalho é válido antes de propagar
    # Importante: Usar a classe BlockchainRules que criamos no Core
    from core.blockchain import BlockchainRules

    if not BlockchainRules.check_pow(header):
        raise HTTPException(status_code=400, detail="Invalid Proof of Work")

    # 3. Salvar Bloco!
    print(f"💰 Bloco Minerado! Height: {candidate_block.height}, Hash: {candidate_block.id}")
    repo.save_block(candidate_block)

    # 4. Limpar Mempool (Removendo APENAS as transações normais, coinbase não estava lá)
    # candidate_block.transactions[1:] pula a coinbase
    mempool.remove_transactions(candidate_block.transactions[1:])

    # 5. Limpar Jobs antigos (Opcional, ou deixa expirar)
    mining_jobs.clear()

    return {"status": "success", "block_hash": candidate_block.id}
