import datetime
import hashlib
import json
from http import HTTPStatus
from pathlib import Path

import requests

from pycoin.settings import Settings

settings = Settings()


def create_genesis_block():
    # Cria o bloco gênesis (primeiro bloco)
    return [{
        'index': 0,
        'timestamp': str(datetime.datetime.now()),
        'previous_hash': '0',
        'hash': calculate_hash({'block_geneses': '0'}),
        'proof': 100,
        'transactions': [],
    }]


def load_chain(block_file_path: Path):
    """
    Carrega os a blockchain de um arquivo JSON. Caso o contrario gere o bloco geneses.
    """
    if not isinstance(block_file_path, Path):
        raise ValueError("O parâmetro block_file_path deve ser um objeto do tipo Path.")

    block_file_path.parent.mkdir(parents=True, exist_ok=True)
    block_file_path.touch()

    if block_file_path.exists():
        try:
            with open(block_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("Erro ao carregar o arquivo. Retornando lista vazia.")
        except Exception as e:
            print(f"Error: {e}")

    blockchain = create_genesis_block()
    save_blockchain(block_file_path=settings.BLOCK_FILENAME,
                    blockchain=blockchain)
    return blockchain


def save_blockchain(block_file_path: Path, blockchain):
    """
    Salva a blockchain em um arquivo JSON.
    """
    if not isinstance(block_file_path, Path):
        raise ValueError("O parâmetro block_file_path deve ser um objeto do tipo Path.")

    print('Salvando blockchain')
    with open(block_file_path, 'w', encoding='utf-8') as file:
        json.dump(blockchain, file, indent=4)


def load_nodes(nodes_file_path: Path=settings.NODES_FILENAME) -> list:
    """
    Carrega os nós de um arquivo JSON. Caso o arquivo não exista, retorna uma lista vazia.
    """
    if not isinstance(nodes_file_path, Path):
        raise ValueError("O parâmetro nodes_file_path deve ser um objeto do tipo Path.")

    nodes_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Atualiza os nodes
    save_nodes()

    if nodes_file_path.exists():
        try:
            with open(nodes_file_path, 'r', encoding='utf-8') as file:
                return json.load(file).get("nodes", [])
        except json.JSONDecodeError:
            print("Erro ao carregar o arquivo. Retornando lista vazia.")
        except Exception as e:
            print(f"Error in load_nodes:  {e}")

    return []


def save_nodes(nodes_file_path: Path=settings.NODES_FILENAME, 
               list_nodes: list=settings.LIST_NODE_VALID):
    """
    Salva uma lista de nós em um arquivo JSON. Adiciona somente nós válidos.
    """
    if not isinstance(nodes_file_path, Path):
        raise ValueError("O parâmetro nodes_file_path deve ser um objeto do tipo Path.")

    # TODO: check_nodetemporariamente comentado
    #valid_nodes = [node for node in list_nodes if check_node(node)]
    valid_nodes = list_nodes
    print(f"Salvando {len(valid_nodes)} nós válidos.")

    with open(nodes_file_path, 'w', encoding='utf-8') as file:
        json.dump({'nodes': valid_nodes}, file, indent=4)


def check_node(node: str) -> bool:
    """
    Verifica se um nó está acessível via HTTP.
    """
    if node == settings.MY_NODE:
        #return False
        pass
    try:
        response = request_get(f'http://{node}/ping')
        if not response:
            print(f"O node {node} está offline")
            return False
        return response.status_code == HTTPStatus.OK
    except (requests.ConnectionError, requests.Timeout):
        return False
    except requests.RequestException as e:
        print(f"Erro ao verificar nó {node}: {e}")
        return False


def proof_of_work(previous_proof: int):
    new_proof = 1
    check_proof = False
    while check_proof is False:
        hash_operation = hashlib.sha256(
            str(new_proof**2 - previous_proof**2).encode()
        ).hexdigest()
        if hash_operation[:4] == '0000':
            check_proof = True
        else:
            new_proof += 1
    return new_proof


def calculate_hash(block: dict):
    encoded_block = json.dumps(block, sort_keys=True).encode()
    return hashlib.sha256(encoded_block).hexdigest()


def request_get(url: str):
    """
    Realiza uma requisição GET e lida com possíveis erros.
    """
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f'Erro na requisição para {url}: {e}')
        return None


def get_previous_block(block_file_path=settings.BLOCK_FILENAME):
        """
        Obtem o último bloco
        """
        blockchain = load_chain(block_file_path)
        return blockchain[-1]


def is_chain_valid(chain: list) -> bool:
    """
    Cada bloco tem um hash correto.
    Cada bloco aponta para o hash do bloco anterior.
    As transações no bloco são válidas.
    """
    for index in range(len(chain) - 1):
        previous_block = chain[index]
        next_block = chain[index + 1]

        # Checa se o calculo do hash posterior é igual ao do proximo hash
        is_match = next_block['hash'] == calculate_hash(previous_block)
        if not is_match:
            return False

        # Realiza o calculo da prova de trabalho do hash posterior com o proximo hash
        previous_proof = previous_block['proof']
        next_proof = next_block['proof']
        hash_operation = hashlib.sha256(
            str(next_proof**2 - previous_proof**2).encode()
        ).hexdigest()
        if hash_operation[:4] != '0000':
            return False
    return True



def propagate_new_blockchain(chain, 
                            nodes,
                            nodes_updated:list=settings.LIST_NODE_VALID,
                            my_node:str=settings.MY_NODE):
    for node in nodes:
        if not check_node(node) or node == my_node:
            continue
        
        print(f'Verificando propagação: {my_node} ---> {node}')

        try:
            url = f'http://{node}/new_blockchain'
            print(f'Propagação de blocos: {my_node} ---> {node}')
            response = requests.post(url,
                json={'chain': chain, 'nodes_updated': nodes_updated})
            if response.status_code == HTTPStatus.OK:
                print(f'Sucesso ao notificar {node}')
            else:
                print(f'Erro ao notificar {node}: {response.status_code}')
        except Exception as e:
            print(f'Erro ao conectar com {node}: {str(e)}')