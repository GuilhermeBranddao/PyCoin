from app.pycoin import Blockchain
from flask import Flask, jsonify
from uuid import uuid4
from flask import Flask, jsonify, request
from app.wallet import Wallet
from app.transaction import Transaction

app = Flask(__name__)
node_address = str(uuid4()).replace('-', '')
blockchain = Blockchain(nodes_file_path="nodes.json",
                        list_node_valid=["127.0.0.1:5001"],
                        block_file_path='block.json',
                        )

@app.route("/wallet", methods = ['GET'])
def wallet():
    try:
        wallet = Wallet()
        private_key, public_key, address = wallet.generate_strings_key_no_markers()
        
        app.logger.info(f"Carteira gerada com sucesso. Address: {address}")
        
        response = {
            "message": "Dados da sua carteira gerados com sucesso!",
            "private_key": private_key,
            "public_key": public_key,
            "address": address
        }
        return jsonify(response), 200

    except Exception as e:
        app.logger.error(f"Erro ao gerar carteira: {e}")
        
        response = {
            "message": "Erro ao gerar os dados da carteira. Tente novamente mais tarde.",
            "error": str(e)
        }
        return jsonify(response), 500


@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Bloco minerado com sucesso!!!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200

@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'Blockchain Válido'}
    else:
        response = {'message': 'Blockchain Inválido'}
    return jsonify(response), 200

@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['private_key_sender', 'public_key_sender', 'recipient_address','amount']
    if not all(key in json for key in transaction_keys):
        return 'Dados inconsistentes entre as partes', 400

    
    index = blockchain.add_transaction(private_key_sender=json['private_key_sender'],
                                       public_key_sender=json['public_key_sender'],
                                       recipient_address=json['recipient_address'],
                                       amount=json['amount'])
    
    response = {'message': f'Nova transação adicionada ao registro {index}'}
    
    return jsonify(response), 201

@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "Vazio", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'Conexão realizada com sucesso entre os seguintes nós: ',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

@app.route('/replace_chain',methods= ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'Nós atualizados com sucesso',
                    'new_chain' : blockchain.chain}
    else:
        response = {'message': 'Não é necessário atualizar os nós da rede.', 
                   'actual_chain' : blockchain.chain}
    return jsonify(response), 201 

@app.route('/get_actual_chain',methods= ['GET'])
def get_actual_chain():
    response = {'message': 'Nós presente na rede atualmente', 
                    'actual_chain' : blockchain.chain}
    return jsonify(response), 201 

@app.route('/get_balance_and_transactions', methods = ['POST'])
def get_balance_and_transactions():
    json = request.get_json()

    actual_chain = blockchain.chain

    # Itera sobre os blocos da cadeia
    balance = 0
    transactions = []
    for block in actual_chain:
        for transaction in block['transactions']:
            # Verifica se o endereço é o destinatário ou o remetente
            if transaction['recipient_address'] == json["address"]:
                # Adiciona o valor recebido
                balance += transaction['amount']
                transactions.append(transaction)  # Adiciona à lista de transações recebidas
            elif transaction['sender'] == json["address"]:
                # Subtrai o valor enviado
                balance -= transaction['amount']
                transactions.append(transaction) 

    response = {"balance":balance,
        "transactions":transactions}

    return jsonify(response), 201

@app.route('/get_my_nodes',methods= ['GET'])
def get_my_nodes():
    nodes = blockchain.load_nodes()
    response = {"message":"Meus nodes",
                "nodes":nodes}
    return jsonify(response), 201

@app.route('/ping',methods= ['GET'])
def ping():
    response = {'message': 'pong'}
    return jsonify(response), 200

app.run(host = '0.0.0.0', port = 5000, debug=True)
