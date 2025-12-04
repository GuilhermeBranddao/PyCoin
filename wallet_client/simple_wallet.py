import os

# Ajuste se necessário para importar do core
import sys

import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from config import KEY_FILE, NODE_URL

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.transaction import Transaction, TxInput, TxOutput

# TODO: Melhorias
    # - Ao realizar a transação o valor entra na Mempool.
    # - Se você consultar o saldo agora, ainda será 100 (ou 60 se a wallet for esperta e descontar mempool, mas nosso código simples olha pro DB confirmado).
# A transação só é confirmada quando o minerador achar mais um bloco.
# Quando ele minerar o próximo bloco, ele vai incluir sua transação da Mempool.


class Wallet:
    def __init__(self):
        self.private_key = self._load_or_create_key()
        self.public_key = self.private_key.public_key()
        self.address = self._generate_address()
        print("🔑 Carteira Carregada!")
        print(f"📬 Endereço: {self.address}\n")

    def _load_or_create_key(self):
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "rb") as f:
                return serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )
        else:
            print("⚠️ Nenhuma chave encontrada. Gerando nova...")
            key = ec.generate_private_key(ec.SECP256K1(), default_backend())

            # Salva no disco
            with open(KEY_FILE, "wb") as f:
                f.write(key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            return key

    def _generate_address(self):
        """O endereço é o Hash SHA256 da chave pública (simplificado)"""
        pub_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        # Em Bitcoin seria RIPEMD160(SHA256(pub)), aqui usamos SHA256 hex para simplicidade
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(pub_bytes)
        return digest.finalize().hex()

    def get_balance(self):
        """Consulta o Node para saber quanto tenho"""
        try:
            res = requests.get(f"{NODE_URL}/tx/utxo/{self.address}")
            if res.status_code != 200:
                print("Erro ao consultar Node.")
                return [], 0

            utxos = res.json()
            total = sum(u['amount'] for u in utxos)
            return utxos, total
        except Exception as e:
            print(f"Erro de conexão: {e}")
            return [], 0

    def send_transaction(self, recipient: str, amount: int):
        # 1. Seleção de Moedas (Coin Selection)
        utxos, balance = self.get_balance()
        if balance < amount:
            print(f"❌ Saldo Insuficiente. Tem: {balance}, Precisa: {amount}")
            return

        inputs = []
        input_sum = 0

        # Algoritmo simples: Pega UTXOs até cobrir o valor
        for utxo in utxos:
            input_sum += utxo['amount']

            # Recupera a Public Key em formato string para o input
            pub_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).hex()

            inputs.append(TxInput(
                prev_tx_id=utxo['tx_id'],
                output_index=utxo['output_index'],
                public_key=pub_pem,
                signature=""  # Será assinada depois
            ))

            if input_sum >= amount:
                break

        # 2. Cria Outputs (Destino + Troco)
        outputs = [TxOutput(amount=amount, address=recipient)]

        change = input_sum - amount
        if change > 0:
            outputs.append(TxOutput(amount=change, address=self.address))
            print(f"🔄 Troco calculado: {change}")

        # 3. Constroi a Transação
        tx = Transaction(inputs=inputs, outputs=outputs)

        # 4. ASSINATURA (A parte mágica)
        print("✍️  Assinando transação...")
        for i in range(len(tx.inputs)):
            tx.sign_input(i, self.private_key)

        # 5. Envia para a rede
        payload = tx.to_dict()
        # Ajuste fino: O Pydantic espera o formato exato
        # Nosso to_dict já deve estar compatível, mas vamos garantir que inputs tenham signature

        try:
            res = requests.post(f"{NODE_URL}/tx/", json=payload)
            if res.status_code == 201:
                print(f"✅ Sucesso! TX ID: {res.json()['tx_id']}")
            else:
                print(f"❌ Erro do Node: {res.text}")
        except Exception as e:
            print(f"Erro ao enviar: {e}")


# --- CLI Simples ---
if __name__ == "__main__":
    w = Wallet()

    while True:
        print("\n1. Ver Saldo")
        print("2. Enviar Moedas")
        print("3. Sair")
        opt = input("Opção: ")

        if opt == "1":
            _, total = w.get_balance()
            print(f"\n💰 Saldo Atual: {total} coins")

        elif opt == "2":
            dest = input("Destinatário (Endereço): ")
            amount = int(input("Valor: "))
            w.send_transaction(dest, amount)

        elif opt == "3":
            break
