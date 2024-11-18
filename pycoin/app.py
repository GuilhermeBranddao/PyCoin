from uuid import uuid4

from fastapi import FastAPI

from pycoin.pycoin import Blockchain
from pycoin.routers import wallet
from pycoin.schemas import AddTransaction
from pycoin.settings import Settings
import uvicorn

settings = Settings()
app = FastAPI()
node_address = str(uuid4()).replace('-', '')
blockchain = Blockchain()

# Wallet and transactions

app.include_router(wallet.router)

# Miners routes

@app.get('/mine_block')
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)

    block = blockchain.create_block(proof, previous_hash)
    response = {
        'message': 'Bloco minerado com sucesso!!!',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
        'transactions': block['transactions'],
    }
    return response

@app.get('/get_actual_chain')
def get_actual_chain():
    pass

@app.get('/replace_chain')
def replace_chain():
    pass

@app.post('/connect_node')
def connect_node():
    pass

@app.get('/is_valid')
def is_valid():
    pass

@app.get('/get_chain')
def get_chain():
    pass

# Others


@app.get('/get_my_nodes')
def get_my_nodes():
    pass

@app.post('/new_blockchain')
def new_blockchain():
    pass


@app.get('/')
def read_root():
    return {'message': 'Olá Mundo!'}

@app.get('/ping')
def ping():
    response = {'message': 'pong'}
    return response



host, port = settings.MY_NODE.split(":")

print(">>>>>>>")
#uvicorn.run("pycoin.app:app", host=host, port=int(port), 
#            reload=True)