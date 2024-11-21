from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request

from pycoin.blockchain.pycoin import BlockchainInitializer

BlockchainInitializer()

from pycoin.blockchain.tool_blockchain import (
    add_node,
    check_progagate_blockchain,
    create_block,
    is_chain_valid,
    load_chain,
    load_nodes,
    replace_chain,
)
from pycoin.routers import wallet
from pycoin.schemas import NodeListRequest
from pycoin.settings import Settings

settings = Settings()
app = FastAPI()
node_address = str(uuid4()).replace('-', '')


# Wallet and transactions

app.include_router(wallet.router)


# Miners routes
@app.get('/mine_block')
def mine_block():
    block = create_block()
    return block


@app.get('/get_actual_chain')
def get_actual_chain():
    chain = load_chain()
    response = {
        'message': 'Nós presente na rede atualmente',
        'actual_chain': chain,
    }
    return response


@app.get('/replace_chain')
def replace_the_chain():
    is_chain_replaced = replace_chain()
    chain = load_chain()

    if is_chain_replaced:
        response = {
            'message': 'Nós atualizados com sucesso',
            'new_chain': chain,
        }
    else:
        response = {
            'message': 'Não é necessário atualizar os nós da rede.',
            'actual_chain': chain,
        }
    return response


@app.post('/connect_node')
def connect_node(request: NodeListRequest):
    """
    Recebe um dicionário de lista de nós e conecta aos nós informados.
    Exemplo de uso:
        - Enviar uma lista de nós para conectar.
    """

    nodes_request = request.nodes

    if not nodes_request:
        raise HTTPException(status_code=400, detail="A lista de nós não pode ser vazia")

    possible_new_nodes = [f"{node.node_address}:{node.port}" for node in nodes_request]

    add_node(possible_new_nodes=possible_new_nodes)

    nodes = load_nodes()
    response = {
        'message': 'Conexão realizada com sucesso entre os seguintes nós:',
        'total_nodes': list(nodes)
    }

    return response


@app.get('/is_valid')
def is_valid():
    chain = load_chain()
    is_valid = is_chain_valid(chain)
    if is_valid:
        response = {'message': 'Blockchain Válido'}
    else:
        response = {'message': 'Blockchain Inválido'}
    return response


@app.get('/get_chain')
def get_chain():
    chain = load_chain()
    response = {'chain': chain,
                'length': len(chain)}
    return response

# Others


@app.get('/get_my_nodes')
def get_my_nodes():
    nodes = load_nodes()
    response = {'message': 'Meus nodes', 'nodes': nodes}
    return response


@app.post('/new_blockchain')
async def new_blockchain(request: Request):
    json = await request.json()

    response = check_progagate_blockchain(
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
