import datetime
import hashlib
from http import HTTPStatus
from urllib.parse import urlparse

import requests

from pycoin.blockchain.tool_blockchain import (
    load_blockchain,
    load_nodes,
    request_get,
    save_blockchain,
    save_nodes,
)
from pycoin.settings import Settings
from pycoin.transaction import Transaction

transaction = Transaction()
settings = Settings()


class Blockchain:
    def __init__(self,):
        self.block_file_path = settings.BLOCK_FILENAME

        self.nodes_file_path = settings.NODES_FILENAME

        self.nodes = load_nodes(self.nodes_file_path)
        self.my_node = settings.MY_NODE
        self.blockchain = load_blockchain(self.block_file_path)
        self.replace_chain()
        self.transactions = []

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.blockchain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash,
            'transactions': transaction.load_transactions(
                transaction.transactions_file_path),
        }

        transaction.clear_transactions(transaction.transactions_file_path)

        print(f'O node {self.my_node} conseguiu minerar um bloco!!!')
        self.blockchain.append(block)
        save_blockchain(block_file_path=settings.BLOCK_FILENAME,
                        blockchain=self.blockchain)

        # Se comunica com os demais nós dá rede
        self.propagate_new_blockchain(
            blockchain_actual=self.blockchain, nodes_updated=[self.my_node]
        )

        return block

    def get_previous_block(self):
        """
        Obtem o último bloco
        """
        return self.blockchain[-1]

    def is_chain_valid(self, chain):
        """
        Cada bloco tem um hash correto.
        Cada bloco aponta para o hash do bloco anterior.
        As transações no bloco são válidas.
        """
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(
                str(proof**2 - previous_proof**2).encode()
            ).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    def propagate_new_blockchain(self, blockchain_actual, nodes_updated: list):
        for node in self.nodes:
            print(f'Verificando propagação: {self.my_node} ---> {node}')

            if self.my_node not in nodes_updated:
                nodes_updated.append(self.my_node)

            if node not in nodes_updated:
                try:
                    url = f'http://{node}/new_blockchain'
                    print(f'Propagação de blocos: {self.my_node} ---> {node}')
                    response = requests.post(url,
                        json={'chain': blockchain_actual, 'nodes_updated': nodes_updated})
                    if response.status_code == HTTPStatus.OK:
                        print(f'Sucesso ao notificar {node}')
                    else:
                        print(f'Erro ao notificar {node}: {response.status_code}')
                except Exception as e:
                    print(f'Erro ao conectar com {node}: {str(e)}')

    def check_progagate_blockchain(self, new_blockchain, nodes_updated: list):
        """
        Verifica se o bloco propagado é o mais maior
        """
        longest_blockchain = None
        max_length = len(self.blockchain)

        length = len(new_blockchain)
        blockchain = new_blockchain

        # Verifica se a cadeia recebida é válida e maior
        if length > max_length and self.is_chain_valid(blockchain):
            max_length = length
            longest_blockchain = blockchain

        # Substitui a cadeia se uma mais longa for encontrada
        if longest_blockchain:
            self.blockchain = longest_blockchain
            save_blockchain(self.block_file_path)

            if self.my_node not in nodes_updated:
                nodes_updated.append(self.my_node)

            # Continua a propagação
            self.propagate_new_blockchain(
                blockchain_actual=self.blockchain, nodes_updated=nodes_updated
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

    def add_node(self, address):
        parsed_url = urlparse(address)
        new_node = parsed_url.netloc
        if new_node not in self.nodes:
            self.nodes.append(new_node)
            save_nodes()

    def replace_nodes(self, node):
        response = request_get(f'http://{node}/get_my_nodes')
        if response.status_code == HTTPStatus.OK:
            if node not in self.nodes:
                self.nodes.append(node)
            save_nodes()

    def replace_chain(self):
        """
        Substitui a blockchain local pela cadeia mais longa da rede, se encontrada.
        Também garante que a rede esteja conectada e que os novos nós sejam integrados.

        corretamente.
        """
        if not self.nodes:
            print('Nenhum nó disponível na rede para sincronização.')
            return False

        longest_chain = None
        max_length = len(self.blockchain)

        for node in self.nodes:
            try:
                response = request_get(f'http://{node}/get_chain')

                if response.status_code == HTTPStatus.OK:
                    self.replace_nodes(node)
                    node_data = response.json()
                    length = node_data.get('length')
                    chain = node_data.get('chain')

                    # Verifica se a cadeia recebida é válida e maior
                    if length > max_length and self.is_chain_valid(chain):
                        max_length = length
                        longest_chain = chain

            except Exception as e:
                print(f'Erro ao conectar-se ao nó {node}: {e}')

        # Substitui a cadeia se uma mais longa for encontrada
        if longest_chain:
            self.blockchain = longest_chain
            save_blockchain(self.block_file_path)
            print('A cadeia foi substituída pela mais longa disponível.')
            return True
        else:
            print('A cadeia local já é a mais longa ou nenhuma válida foi encontrada.')
            return False
