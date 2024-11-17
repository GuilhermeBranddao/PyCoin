import datetime
import hashlib
import json
import requests
from urllib.parse import urlparse
from pathlib import Path
from app.transaction import Transaction
import os

class Blockchain:
    def __init__(self, 
                 my_node,
                 list_node_valid:list=["127.0.0.1:5000"],
                 block_file_path='block.json', 
                 nodes_file_path="nodes.json"):
        
        self.block_file_path = Path(os.path.join("app", "data", "blockchain", block_file_path))
        self.nodes_file_path = Path(os.path.join("app", "data", "nodes", nodes_file_path))
        self.nodes = self.load_nodes(list_node_valid) 
        self.my_node = my_node
        self.blockchain = self.load_blockchain()
        self.replace_chain()
        self.transactions = []
    
    def create_genesis_block(self):
        # Cria o bloco gênesis (primeiro bloco)
        return {"index": 0, "timestamp": str(datetime.datetime.now()), 
                "previous_hash": "0", "proof": 100, "transactions": []}

    def load_blockchain(self):
        if self.block_file_path.exists():
            with open(self.block_file_path, 'r') as file:
                return json.load(file)
        else:
            self.block_file_path.parent.mkdir(parents=True, exist_ok=True)
            self.blockchain = [self.create_genesis_block()]
            self.save_blockchain()
            return self.blockchain
        
    def save_blockchain(self):
        with open(self.block_file_path, 'w') as file:
            json.dump(self.blockchain, file, indent=4)

    def load_nodes(self, list_node_valid:list=[]):
        # FIXME: Não faz sentido o load_nodes receber uma lista de nodes pra salvar... :-(
        if self.nodes_file_path.exists():
            with open(self.nodes_file_path, 'r') as file:
                return json.load(file)
        else:
            self.nodes_file_path.parent.mkdir(parents=True, exist_ok=True)
            self.nodes = {"nodes":list_node_valid}
            has_node = self.check_node(list_node_valid)
            if not has_node:
                #raise ValueError("O node não existe.")
                print("Esse node ainda não existe, mas por enquanto tudo bem :-)")
            self.save_nodes()
            return self.nodes
        
    def save_nodes(self):
        with open(self.nodes_file_path, 'w') as file:
            json.dump(self.nodes, file, indent=4)

    def check_node(self, node):
        """
        Checa de node existe
        """
        try: 
            response = requests.get(f'http://{node}/ping')

            if response.status_code == 200:
                return True
            else:
                return False
        except:
            return False
    
    def create_block(self, proof, previous_hash):

        block = {'index': len(self.blockchain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'transactions': self.transactions}
        self.transactions = []

        self.blockchain.append(block)
        self.save_blockchain()

        # Se comunica com os demais nós dá rede
        self.propagate_new_blockchain(blockchain_actual=self.blockchain, nodes_updated=self.nodes)

        return block

    def get_previous_block(self):
        """
        Obtem o último bloco
        """
        return self.blockchain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
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
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    def add_transaction(self, private_key_sender, public_key_sender, recipient_address, amount):

        transaction = Transaction(private_key_sender=private_key_sender,
                                public_key_sender=public_key_sender,
                                recipient_address=recipient_address, 
                                amount=amount)
        
        # Usuário A assina a transação
        transaction.sign_transaction()

        encoded_data = transaction._decode_transaction_data(transaction._get_transaction_data())

        self.transactions.append(encoded_data)

        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def propagate_new_blockchain(self, blockchain_actual, nodes_updated):
        for node in self.nodes["nodes"]:
            if self.my_node != node:
                try:
                    url = f'http://{node}/new_block'
                    print(f"Propagação de blocos: {self.my_node} ---> {node}")

                    response = requests.post(url, json={"chain": blockchain_actual,
                                                        "nodes_updated":[nodes_updated]})
                    if response.status_code == 200:
                        print(f'Sucesso ao notificar {node}')
                    else:
                        print(f'Erro ao notificar {node}: {response.status_code}')
                except Exception as e:
                    print(f'Erro ao conectar com {node}: {str(e)}')
    
    def check_progagate_blockchain(self, new_blockchain, nodes_updated):
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
            self.save_blockchain()

            nodes_updated.append(self.my_node)

            # Continua a propagação
            self.propagate_new_blockchain(blockchain_actual=self.blockchain, nodes_updated=nodes_updated)
            print("A cadeia foi substituída pela mais longa disponível.")
            return True
        else:
            print("A cadeia local já é a mais longa ou nenhuma cadeia válida foi encontrada.")
            return False


    def add_node(self, address):
        parsed_url = urlparse(address)
        new_node = parsed_url.netloc
        if new_node not in self.nodes['nodes']:
            self.nodes['nodes'].append(new_node)
            self.save_nodes()
    
    def replace_nodes(self, node):
        response = self.request_get(f'http://{node}/get_my_nodes')
        if response.status_code == 200:
            if node not in self.nodes['nodes']:
                self.nodes['nodes'].append(node)
            self.save_nodes()

    def replace_chain(self):
        """
        Substitui a blockchain local pela cadeia mais longa da rede, se encontrada.
        Também garante que a rede esteja conectada e que os novos nós sejam integrados corretamente.
        """
        if not self.nodes['nodes']:
            print("Nenhum nó disponível na rede para sincronização.")
            return False

        longest_chain = None
        max_length = len(self.blockchain)

        for node in self.nodes['nodes']:
            try:
                response = self.request_get(f'http://{node}/get_chain')
                
                if response.status_code == 200:
                    self.replace_nodes(node)
                    node_data = response.json()
                    length = node_data.get('length')
                    chain = node_data.get('chain')
                    
                    # Verifica se a cadeia recebida é válida e maior
                    if length > max_length and self.is_chain_valid(chain):
                        max_length = length
                        longest_chain = chain

            except Exception as e:
                print(f"Erro ao conectar-se ao nó {node}: {e}")

        # Substitui a cadeia se uma mais longa for encontrada
        if longest_chain:
            self.blockchain = longest_chain
            self.save_blockchain()
            print("A cadeia foi substituída pela mais longa disponível.")
            return True
        else:
            print("A cadeia local já é a mais longa ou nenhuma cadeia válida foi encontrada.")
            return False

    def request_get(self, url):
        """
        Realiza uma requisição GET e lida com possíveis erros.
        """
        try:
            response = requests.get(url, timeout=5)  # Timeout para evitar longos tempos de espera
            response.raise_for_status()  # Levanta exceção para códigos de status não 2xx
            return response
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição para {url}: {e}")
            return None

