# Exemplo conceitual de como o core/utxo.py deve tratar os dados
class UTXO:
    def __init__(self, tx_hash: str, output_index: int, amount: int, script_pub_key: str):
        self.tx_hash = tx_hash          # Hash da transação que criou essa saída
        self.output_index = output_index  # Qual das saídas dessa tx é essa moeda (0, 1, 2...)
        self.amount = amount
        self.script_pub_key = script_pub_key  # O "cadeado" (quem pode gastar)
