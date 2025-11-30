import asyncio
import datetime
import hashlib
import json
import random
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlparse

import requests

from pycoin.settings.config import Settings
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


def load_chain(block_file_path: Path = settings.BLOCKCHAIN_FILE) -> list:
    """
    Carrega os a blockchain de um arquivo JSON. Caso o contrario gere o bloco geneses.
    """
    if not isinstance(block_file_path, Path):
        raise ValueError("O parâmetro block_file_path deve ser um objeto do tipo Path.")

    if block_file_path.exists():
        try:
            with open(block_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("Erro ao carregar o arquivo chain. Retornando lista vazia.")
        except Exception as e:
            print(f"Error: {e}")


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


def load_nodes(nodes_file_path: Path = settings.NODES_FILE) -> list:
    """
    Carrega os nós de um arquivo JSON. Caso o arquivo não exista, retorna uma lista vazia.
    """
    if not isinstance(nodes_file_path, Path):
        raise ValueError("O parâmetro nodes_file_path deve ser um objeto do tipo Path.")

    if nodes_file_path.exists():
        try:
            with open(nodes_file_path, 'r', encoding='utf-8') as file:
                return json.load(file).get("nodes", [])
        except json.JSONDecodeError:
            print("Erro ao carregar o arquivo de nodes. Retornando lista vazia.")
        except Exception as e:
            print(f"Error in load_nodes:  {e}")

    return []


def save_nodes(nodes_file_path: Path = settings.NODES_FILE,
               list_new_nodes: list = settings.LIST_NODE_VALID) -> None:
    """
    Salva uma lista de nós em um arquivo JSON. Adiciona somente nós válidos.
    """
    if not isinstance(nodes_file_path, Path):
        raise ValueError("O parâmetro nodes_file_path deve ser um objeto do tipo Path.")

    existing_node = load_nodes(nodes_file_path=nodes_file_path)
    new_nodes = set(list_new_nodes + existing_node)

    print(f"Salvando {len(new_nodes)} nós válidos.")

    with open(nodes_file_path, 'w', encoding='utf-8') as file:
        json.dump({'nodes': list(new_nodes)}, file, indent=4)

    return True


def check_node(node: str) -> bool:
    """
    Verifica se um nó está acessível via HTTP.
    """
    if node == settings.MY_NODE:
        return False
    return False
    try:
        response = request_get(f'http://{node}/ping')
        if not response:
            print(f"O node {node} está offline")
            return False

        print(f"O node {node} está online")
        return response.status_code == HTTPStatus.OK
    except (requests.ConnectionError, requests.Timeout):
        return False
    except requests.RequestException as e:
        print(f"Erro ao verificar nó {node}: {e}")
        return False


def request_get(url: str):
    """
    Realiza uma requisição GET e lida com possíveis erros.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException:
        return None


def get_previous_block(block_file_path: str = settings.BLOCKCHAIN_FILE) -> dict:
        """
        Obtem o último bloco
        """
        blockchain = load_chain(block_file_path)
        return blockchain[-1]


async def proof_of_work(previous_block: dict, difficulty: int = 4, is_sleep=True) -> int:
    """
    Gera a prova de trabalho com base na dificuldade fornecida de forma assíncrona.

    :param previous_block: A prova do bloco anterior.
    :param difficulty: Número de zeros iniciais necessários no hash.
    :param is_sleep: Se deve simular uma pausa durante a mineração.
    :return: O novo proof.
    """
    new_proof = 0
    prefix = '0' * difficulty  # Define a meta baseada na dificuldade

    if is_sleep:
        # Substituímos o sleep bloqueante por await asyncio.sleep
        segundos = random.randint(2, 6)
        print(f'Esperendo por {segundos} segundos')
        await asyncio.sleep(segundos)  # Faz uma pausa de forma assíncrona

    while True:
        # Realiza o cálculo do hash
        block_candidate = {
            "index": previous_block["index"] + 1,
            "timestamp": str(datetime.datetime.now()),
            "proof": new_proof,
            "previous_hash": previous_block["hash"],
            "transactions": []  # transações serão adicionadas depois
        }

        hash_value = calculate_hash(block_candidate)

        if hash_value.startswith(prefix):
            block_candidate["hash"] = hash_value
            return block_candidate

        new_proof += 1


def calculate_hash(block: dict) -> str:
    """
    Calcula o hash SHA-256 de um bloco (sem o campo hash).

    :param block: Dicionário contendo os dados do bloco.
    :return: Hash SHA-256 do bloco.
    """
    block_copy = block.copy()
    block_copy.pop("hash", None)
    block_string = json.dumps(block_copy, sort_keys=True).encode()
    return hashlib.sha256(block_string).hexdigest()


def is_chain_valid(chain: list, difficulty: int = 4) -> bool:
    """
    Verifica a validade de uma blockchain.

    Para validar de forma automática, precisamos checar três coisas principais:
    - Integridade dos hashes: o hash armazenado deve bater com o cálculo real do bloco.
    - Encadeamento: previous_hash de cada bloco deve ser igual ao hash do bloco anterior.
    - Proof of Work: o valor de proof deve satisfazer a regra definida (ex.: hash começando com 0000).
    - Timestamp coerente

    :param chain: Lista de blocos representando a blockchain.
    :param difficulty: Dificuldade esperada para a prova de trabalho.
    :return: True se a blockchain for válida, False caso contrário.
    """

    if not chain or len(chain) == 0:
        logger.error("Blockchain vazia")
        return False

    prefix = "0" * difficulty

    for index in range(1, len(chain)):
        current_block = chain[index]
        previous_block = chain[index - 1]

        # 1. Verifica integridade do hash
        recalculated_hash = calculate_hash(current_block)
        if current_block.get("hash") != recalculated_hash:
            logger.error(f"❌ Hash inválido no bloco {current_block.get('index')}")
            return False

        # 2. Verifica encadeamento
        if current_block.get("previous_hash") != previous_block.get("hash"):
            logger.error(f"❌ Encadeamento inválido no bloco {current_block.get('index')}")
            return False

        # 3. Verifica Proof of Work
        if not current_block["hash"].startswith(prefix):
            logger.error(f"⚠️ Prova de trabalho inválida no bloco {current_block.get('index')}")
            return False

        # 4. Verifica timestamp coerente
        try:
            current_time = datetime.datetime.fromisoformat(current_block["timestamp"])
            previous_time = datetime.datetime.fromisoformat(previous_block["timestamp"])
            if current_time < previous_time:
                logger.error(f"⏱️ Timestamp inválido no bloco {current_block.get('index')}")
                return False
        except Exception as e:
            logger.error(f"Erro ao validar timestamp: {e}")
            return False

    logger.info("✅ Blockchain válida")
    return True


def propagate_new_blockchain(chain,
                            nodes,
                            nodes_updated: list = settings.LIST_NODE_VALID,
                            my_node: str = settings.NODES_FILE):
    for node in nodes:
        if not check_node(node) or node == my_node:
            continue

        print(f'Verificando propagação: {my_node} ---> {node}')

        try:
            url = f'http://{node}/miner/new_blockchain'
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


def update_blockchain(block_file_path: Path = settings.BLOCKCHAIN_FILE) -> bool:
    """
    Atualiza a blockchain local pela cadeia mais longa da rede, se encontrada.
    Também garante que a rede esteja conectada e que os novos nós sejam integrados.
    """
    nodes = load_nodes()

    if not nodes:
        print('Nenhum nó disponível na rede para sincronização.')
        return False

    longest_chain = None
    chain = load_chain(block_file_path)
    max_length = len(chain)

    for node in nodes:
        if not check_node(node):
            continue

        try:
            response = request_get(f'http://{node}/miner/get_chain')
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
            block_file_path=block_file_path)
        print('A cadeia foi substituída pela mais longa disponível.')
        return True

    print('A cadeia local já é a mais longa ou nenhuma válida foi encontrada.')
    return False


import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def start_block_mining(
    block_file_path: Path = settings.BLOCKCHAIN_FILE,
    transactions_file_path: Path = settings.TRANSACTIONS_FILE
) -> dict | None:
    """
    Inicia o processo de mineração de um novo bloco.
    Responsabilidades:
    - Recuperar o último bloco
    - Executar prova de trabalho
    - Validar a cadeia existente
    - Criar e salvar novo bloco
    - Propagar atualização para os nós da rede
    """

    try:
        previous_block = get_previous_block(block_file_path)
        new_block = await proof_of_work(previous_block)

        chain = load_chain(block_file_path)
        chain.append(new_block)

        if not is_chain_valid(chain):
            logger.warning("Blockchain inválida. Atualizando...")
            update_blockchain()
            return None

        # Adiciona recompensa ao minerador
        Transaction.add_transaction_miner_reward(
            miner_address=settings.MINER_PUBLIC_ADDRESS,
            reward_amount=settings.MINING_REWARD
        )

        # Cria novo bloco
        # block = create_new_block(
        #     chain=chain,
        #     previous_block=previous_block,
        #     proof=proof,
        #     transactions_file_path=transactions_file_path
        # )

        # Persiste e propaga
        save_blockchain(block_file_path, chain)
        propagate_to_network(chain)

        logger.info(f"Nó {settings.NODES_FILE} minerou um novo bloco #{new_block['index']}")
        return {"new_block": new_block}

    except Exception as e:
        logger.error(f"Erro ao minerar o bloco: {e}", exc_info=True)
        return None


def create_new_block(chain: list, previous_block: dict, proof: int, transactions_file_path: Path) -> dict:
    """Cria um novo bloco e adiciona à cadeia."""
    block = {
        "index": len(chain),
        "timestamp": datetime.datetime.now().isoformat(),
        "proof": proof,
        "previous_hash": previous_block["hash"],
        "transactions": Transaction.load_transactions(transactions_file_path),
    }
    block["hash"] = calculate_hash(block)

    # Limpa transações pendentes
    Transaction.clear_transactions(transactions_file_path)

    chain.append(block)
    return block


def propagate_to_network(chain: list) -> None:
    """Propaga a blockchain atualizada para os nós da rede."""
    nodes = load_nodes()
    propagate_new_blockchain(chain=chain, nodes=nodes)


def check_progagate_blockchain(new_blockchain,
                               nodes_updated: list,
                               block_file_path: Path = settings.BLOCKCHAIN_FILE,):
    """
    Verifica se o bloco propagado é o mais maior
    """

    chain = load_chain(block_file_path)

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
                        block_file_path=settings.BLOCKCHAIN_FILE)

        if settings.NODES_FILE not in nodes_updated:
            nodes_updated.append(settings.NODES_FILE)

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
