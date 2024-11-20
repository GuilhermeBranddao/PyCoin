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
        'proof': 100,
        'transactions': [],
    }]


def load_blockchain(block_file_path: Path):
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
        except:
            print("Erro desconhecido")

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


def load_nodes(nodes_file_path: Path) -> list:
    """
    Carrega os nós de um arquivo JSON. Caso o arquivo não exista, retorna uma lista vazia.
    """
    if not isinstance(nodes_file_path, Path):
        raise ValueError("O parâmetro nodes_file_path deve ser um objeto do tipo Path.")

    nodes_file_path.parent.mkdir(parents=True, exist_ok=True)

    if nodes_file_path.exists():
        try:
            with open(nodes_file_path, 'r', encoding='utf-8') as file:
                return json.load(file).get("nodes", [])
        except json.JSONDecodeError:
            print("Erro ao carregar o arquivo. Retornando lista vazia.")
        except:
            print("Erro desconhecido")

    return []


def save_nodes(nodes_file_path: Path, list_nodes: list):
    """
    Salva uma lista de nós em um arquivo JSON. Adiciona somente nós válidos.
    """
    if not isinstance(nodes_file_path, Path):
        raise ValueError("O parâmetro nodes_file_path deve ser um objeto do tipo Path.")

    valid_nodes = [node for node in list_nodes if check_node(node)]
    print(f"Salvando {len(valid_nodes)} nós válidos.")

    with open(nodes_file_path, 'w', encoding='utf-8') as file:
        json.dump({'nodes': valid_nodes}, file, indent=4)


def check_node(node: str) -> bool:
    """
    Verifica se um nó está acessível via HTTP.
    """
    try:
        response = requests.get(f'http://{node}/ping', timeout=5)
        return response.status_code == HTTPStatus.OK
    except (requests.ConnectionError, requests.Timeout):
        return False
    except requests.RequestException as e:
        print(f"Erro ao verificar nó {node}: {e}")
        return False


def proof_of_work(previous_proof):
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


def hash(block):
    encoded_block = json.dumps(block, sort_keys=True).encode()
    return hashlib.sha256(encoded_block).hexdigest()


def request_get(url):
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
