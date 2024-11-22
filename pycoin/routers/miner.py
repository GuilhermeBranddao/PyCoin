from fastapi import APIRouter, HTTPException, Request

from pycoin.blockchain.tool_blockchain import (
    add_node,
    check_progagate_blockchain,
    is_chain_valid,
    load_chain,
    load_nodes,
    start_block_mining,
    update_blockchain,
)

from pycoin.miner.miner_manager import MinerManager
from pycoin.schemas import NodeListRequest
from pycoin.settings import Settings

# Instância do gerenciador
miner_manager = MinerManager()  
settings = Settings()
router = APIRouter(prefix='/miner', tags=['miner'])


@router.get('/start_mining')
async def start_mining():
    result = await miner_manager.start_mining(start_block_mining)
    return {"message": result}

@router.get('/stop_mining')
async def stop_mining():
    result = await miner_manager.stop_mining()
    return {"message": result}

@router.get('/get_actual_chain')
def get_actual_chain():
    chain = load_chain()
    response = {
        'message': 'Nós presente na rede atualmente',
        'actual_chain': chain,
    }
    return response


@router.get('/update_blockchain')
def replace_the_chain():
    is_chain_replaced = update_blockchain()
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


@router.post('/connect_node')
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


@router.get('/is_valid')
def is_valid():
    chain = load_chain()
    is_valid = is_chain_valid(chain)
    if is_valid:
        response = {'message': 'Blockchain Válido'}
    else:
        response = {'message': 'Blockchain Inválido'}
    return response


@router.get('/get_chain')
def get_chain():
    chain = load_chain()
    response = {'chain': chain,
                'length': len(chain)}
    return response


@router.get('/get_my_nodes')
def get_my_nodes():
    nodes = load_nodes()
    response = {'message': 'Meus nodes', 'nodes': nodes}
    return response


@router.post('/new_blockchain')
async def new_blockchain(request: Request):
    json = await request.json()

    response = check_progagate_blockchain(
        new_blockchain=json['chain'],
        nodes_updated=json['nodes_updated'])

    return response
