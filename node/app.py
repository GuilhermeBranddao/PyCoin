# node/app.py
from fastapi import FastAPI, Depends
from node.routes import tx, mining
from node.services.mempool_service import MempoolService
from node.storage.chain_repository import ChainRepository

# Inicialização dos Singletons (Serviços Únicos)
# Na prática real, use o sistema de 'lifespan' do FastAPI ou uma lib de DI
chain_repo = ChainRepository()
mempool_service = MempoolService(chain_repository=chain_repo)

app = FastAPI(title="PyCoin Node")

# Função de dependência para injetar o mempool
def get_mempool():
    return mempool_service

# Função de dependência para injetar o repositório
def get_chain_repo():
    return chain_repo

# Registra as rotas
app.include_router(tx.router)
app.include_router(mining.router)

@app.lifespan("startup")
async def startup_event():
    print("Node iniciado. Carregando UTXO set...")
    # Aqui você poderia carregar o UTXO em memória se necessário
    
@app.lifespan("shutdown")
def shutdown_event():
    chain_repo.close()