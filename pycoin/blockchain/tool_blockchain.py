import datetime
import hashlib
import json
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlparse

import requests

from pycoin.settings import Settings
from pycoin.transaction import Transaction

settings = Settings()


def create_genesis_block() -> list:
    # Cria o bloco gênesis (primeiro bloco)
    return [{
        'index': 0,
        'timestamp': str(datetime.datetime.now()),
        'previous_hash': '0',
        'hash': calculate_hash({'block_geneses': '0'}),
        'proof': 100,
        'transactions': [],
    }]


def load_chain(block_file_path: Path = settings.BLOCK_FILENAME) -> list:
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


def save_blockchain(block_file_path: Path, blockchain) -> bool:
    """
    Salva a blockchain em um arquivo JSON.
    """
    if not isinstance(block_file_path, Path):
        raise ValueError("O parâmetro block_file_path deve ser um objeto do tipo Path.")

    print('Salvando blockchain')
    with open(block_file_path, 'w', encoding='utf-8') as file:
        json.dump(blockchain, file, indent=4)

    return True


def load_nodes(nodes_file_path: Path = settings.NODES_FILENAME) -> list:
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


def save_nodes(nodes_file_path: Path = settings.NODES_FILENAME,
               list_nodes: list = settings.LIST_NODE_VALID) -> None:
    """
    Salva uma lista de nós em um arquivo JSON. Adiciona somente nós válidos.
    """
    if not isinstance(nodes_file_path, Path):
        raise ValueError("O parâmetro nodes_file_path deve ser um objeto do tipo Path.")

    # TODO: check_nodetemporariamente comentado
    # valid_nodes = [node for node in list_nodes if check_node(node)]
    valid_nodes = list_nodes
    print(f"Salvando {len(valid_nodes)} nós válidos.")

    with open(nodes_file_path, 'w', encoding='utf-8') as file:
        json.dump({'nodes': valid_nodes}, file, indent=4)


def check_node(node: str) -> bool:
    """
    Verifica se um nó está acessível via HTTP.
    """
    if node == settings.MY_NODE:
        # return False
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


def get_previous_block(block_file_path: str = settings.BLOCK_FILENAME) -> dict:
        """
        Obtem o último bloco
        """
        blockchain = load_chain(block_file_path)
        return blockchain[-1]


def proof_of_work(previous_proof: int, difficulty: int = 4) -> int:
    """
    Gera a prova de trabalho com base na dificuldade fornecida.

    :param previous_proof: A prova do bloco anterior.
    :param difficulty: Número de zeros iniciais necessários no hash.
    :return: O novo proof.
    """
    target = '0' * difficulty  # Define a meta baseada na dificuldade
    new_proof = 1

    while True:
        hash_operation = hashlib.sha256(
            f"{new_proof**2 - previous_proof**2}".encode()
        ).hexdigest()
        if hash_operation[:difficulty] == target:
            return new_proof
        new_proof += 1


def calculate_hash(block: dict) -> str:
    """
    Calcula o hash de um bloco.

    :param block: Dicionário contendo os dados do bloco.
    :return: Hash SHA-256 do bloco.
    """
    block_string = str(block).encode()
    return hashlib.sha256(block_string).hexdigest()


def is_chain_valid(chain: list, difficulty: int = 4) -> bool:
    """
    Verifica a validade de uma blockchain.

    :param chain: Lista de blocos representando a blockchain.
    :param difficulty: Dificuldade esperada para a prova de trabalho.
    :return: True se a blockchain for válida, False caso contrário.
    """
    for index in range(1, len(chain)):
        previous_block = chain[index - 1]
        current_block = chain[index]

        # Verifica o hash do bloco anterior
        if current_block['previous_hash'] != calculate_hash(previous_block):
            return False

        # Verifica a prova de trabalho do bloco atual
        previous_proof = previous_block['proof']
        current_proof = current_block['proof']
        hash_operation = hashlib.sha256(
            f"{current_proof**2 - previous_proof**2}".encode()
        ).hexdigest()
        if hash_operation[:difficulty] != '0' * difficulty:
            return False

    return True


def propagate_new_blockchain(chain,
                            nodes,
                            nodes_updated: list = settings.LIST_NODE_VALID,
                            my_node: str = settings.MY_NODE):
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


def add_node(possible_new_nodes: list) -> None:
    nodes = []
    if node not in possible_new_nodes:
        parsed_url = urlparse(node)
        node = parsed_url.netloc
        nodes.append(node)

    save_nodes(list_nodes=nodes)


def replace_chain() -> bool:
    """
    Substitui a blockchain local pela cadeia mais longa da rede, se encontrada.
    Também garante que a rede esteja conectada e que os novos nós sejam integrados.

    corretamente.
    """
    nodes = load_nodes()

    if not nodes:
        print('Nenhum nó disponível na rede para sincronização.')
        return False

    longest_chain = None
    chain = load_chain()
    max_length = len(chain)

    for node in nodes:
        if not check_node(node):
            continue

        try:
            response = request_get(f'http://{node}/get_chain')
            if response.status_code == HTTPStatus.OK:
                node_data = response.json()
                length = node_data.get('length')
                chain = node_data.get('chain')

                # Verifica se a cadeia recebida é válida e maior
                if length > max_length and is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain

        except Exception as e:
            print(f'Erro ao conectar-se ao nó {node}: {e}')

    # Substitui a cadeia se uma mais longa for encontrada
    if longest_chain:
        chain = longest_chain
        save_blockchain(blockchain=chain,
            block_file_path=settings.BLOCK_FILENAME)
        print('A cadeia foi substituída pela mais longa disponível.')
        return True

    print('A cadeia local já é a mais longa ou nenhuma válida foi encontrada.')
    return False


def create_block():
    # TODO: Validação dos blocos existentes
    # TODO: Verifica se não há blocos já minerados

    chain = load_chain()

    previous_block = get_previous_block()

    Transaction.add_transaction_miner_reward(
        miner_address=settings.MINER_PUBLIC_ADDRESS,
        reward_amount=settings.MINING_REWARD)

    block = {
        'index': len(chain),
        'timestamp': str(datetime.datetime.now()),
        'proof': proof_of_work(previous_proof=previous_block['proof']),
        'hash': calculate_hash(previous_block),
        'previous_hash': previous_block['hash'],
        'transactions': Transaction.load_transactions(settings.TRANSACTION_FILENAME),
    }
    Transaction.clear_transactions(settings.TRANSACTION_FILENAME)

    print(f'O node {settings.MY_NODE} conseguiu minerar um bloco!!!')
    chain.append(block)

    save_blockchain(block_file_path=settings.BLOCK_FILENAME,
                    blockchain=chain)

    # Se comunica com os demais nós dá rede
    nodes = load_nodes()
    propagate_new_blockchain(
        chain=chain,
        nodes=nodes,
    )

    return block


def check_progagate_blockchain(new_blockchain,
                                   nodes_updated: list):
    """
    Verifica se o bloco propagado é o mais maior
    """

    chain = load_chain()

    longest_blockchain = None
    max_length = len(chain)

    length = len(new_blockchain)
    blockchain = new_blockchain

    # Verifica se a cadeia recebida é válida e maior
    if length > max_length and is_chain_valid(blockchain):
        max_length = length
        longest_blockchain = blockchain

    # Substitui a cadeia se uma mais longa for encontrada
    if longest_blockchain:
        chain = longest_blockchain
        save_blockchain(blockchain=chain,
                        block_file_path=settings.BLOCK_FILENAME)

        if settings.MY_NODE not in nodes_updated:
            nodes_updated.append(settings.MY_NODE)

        # Continua a propagação
        nodes = load_nodes()
        propagate_new_blockchain(
            chain=chain, nodes=nodes
        )

        print('A cadeia foi substituída pela mais longa disponível.')
        response = {
            'message': 'A cadeia foi substituída pela mais longa disponível.',
            'new_blockchain': new_blockchain,
            'nodes_updated': nodes_updated,
        }
        return response
    else:
        print('A cadeia local já é a mais longa ou nenhuma cadeia foi encontrada.')
        response = {
            'message': 'A cadeia local já é a mais longa.',
            'new_blockchain': [],
            'nodes_updated': [],
        }
        return response
