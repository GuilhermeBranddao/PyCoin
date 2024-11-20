from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request

from pycoin.blockchain.pycoin import Blockchain
from pycoin.blockchain.tool_blockchain import hash, proof_of_work
from pycoin.routers import wallet
from pycoin.schemas import NodeListRequest
from pycoin.settings import Settings

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
    proof = proof_of_work(previous_proof)
    previous_hash = hash(previous_block)
    # TODO: Adicionar hash atual
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
    response = {
        'message': 'Nós presente na rede atualmente',
        'actual_chain': blockchain.blockchain,
    }
    return response


@app.get('/replace_chain')
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {
            'message': 'Nós atualizados com sucesso',
            'new_chain': blockchain.blockchain,
        }
    else:
        response = {
            'message': 'Não é necessário atualizar os nós da rede.',
            'actual_chain': blockchain.blockchain,
        }
    return response


@app.post('/connect_node')
def connect_node(request: NodeListRequest):
    """
    Recebe um dicionário de lista de nós e conecta aos nós informados.
    Exemplo de uso:
        - Enviar uma lista de nós para conectar.
    """
    nodes = request.nodes
    if not nodes:
        raise HTTPException(status_code=400, detail="A lista de nós não pode ser vazia")

    for node in nodes:
        # Simula a adição do nó ao blockchain
        blockchain.add_node(f"{node.node_address}:{node.port}")

    response = {
        'message': 'Conexão realizada com sucesso entre os seguintes nós:',
        'total_nodes': list(blockchain.nodes)
    }

    return response


@app.get('/is_valid')
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.blockchain)
    if is_valid:
        response = {'message': 'Blockchain Válido'}
    else:
        response = {'message': 'Blockchain Inválido'}
    return response


@app.get('/get_chain')
def get_chain():
    response = {'chain': blockchain.blockchain,
                'length': len(blockchain.blockchain)}
    return response

# Others


@app.get('/get_my_nodes')
def get_my_nodes():
    nodes = blockchain.load_nodes()
    response = {'message': 'Meus nodes', 'nodes': nodes}
    return response


@app.post('/new_blockchain')
def new_blockchain(request: Request):
    json = request.json()

    response = blockchain.check_progagate_blockchain(
        new_blockchain=json['chain'],
        nodes_updated=json['nodes_updated'])

    return response


@app.get('/ping')
def ping():
    response = {'message': 'pong'}
    return response

# host, port = settings.MY_NODE.split(":")
# uvicorn.run("pycoin.app:app", host=host, port=int(port),
#            reload=True)
