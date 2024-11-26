from pathlib import Path

from pycoin.settings.config import Settings
from pycoin.utils.file_initializers import (
    initialize_blockchain_file,
    initialize_node_file,
    initialize_transaction_file,
)

settings = Settings()


class BlockchainInitializer:
    def __init__(self,
                nodes_file_path: Path = settings.NODES_FILE,
                block_file_path: Path = settings.BLOCKCHAIN_FILE,
                transaction_file_path: Path = settings.TRANSACTIONS_FILE):
        # TODO: Add verificação de os arquivos podem ser abertos
            # Evitar esse de json criado pela metade
            # Erro ao minerar o bloco: Object of type coroutine is not JSON serializable
            # Se o json estiver corrompido criar outro zerado

        # Inicialização dos arquivos
        initialize_node_file(nodes_file_path=nodes_file_path)
        initialize_blockchain_file(block_file_path=block_file_path)
        initialize_transaction_file(transaction_file_path=transaction_file_path)
        # load_chain(settings.NODES_FILE)
        # replace_chain()
