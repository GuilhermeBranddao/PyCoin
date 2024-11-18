from uuid import uuid4

from fastapi import FastAPI

from pycoin.pycoin import Blockchain
from pycoin.routers import wallet

app = FastAPI()
node_address = str(uuid4()).replace('-', '')
blockchain = Blockchain(
    nodes_file_path='nodes.json',
    list_node_valid=['127.0.0.1:5001'],
    block_file_path='block.json',
    my_node='127.0.0.1:5000',
)

app.include_router(wallet.router)


@app.get('/')
def read_root():
    return {'message': 'Olá Mundo!'}
