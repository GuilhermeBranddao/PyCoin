from uuid import uuid4

from fastapi import FastAPI

from pycoin.blockchain.pycoin import BlockchainInitializer
from pycoin.routers import miner, wallet
from pycoin.settings import Settings

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

# host, port = settings.MY_NODE.split(":")
# uvicorn.run("pycoin.app:app", host=host, port=int(port),
#            reload=True)
