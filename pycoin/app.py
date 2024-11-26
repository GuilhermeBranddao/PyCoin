from uuid import uuid4

from fastapi import FastAPI

from pycoin.blockchain.blockchain_manager import BlockchainInitializer
from pycoin.routers import miner, wallet
from pycoin.settings.config import Settings

BlockchainInitializer()

settings = Settings()
app = FastAPI()
node_address = str(uuid4()).replace('-', '')

app.include_router(wallet.router)
app.include_router(miner.router)


@app.get('/ping')
def ping():
    response = {'message': 'pong'}
    return response


@app.get('/status')
def status():
    response = {'online': True,  # Se está conectado a outros blocos onlines
            'mining': True,
            'date_lest_update_block': 0,  # timestemp do ultimo bloco minerado
            'qtd_block_mining': 0,
            'qtd_coins_earned': 0}
    return response

# host, port = settings.MY_NODE.split(":")
# uvicorn.run("pycoin.app:app", host=host, port=int(port),
#            reload=True)
