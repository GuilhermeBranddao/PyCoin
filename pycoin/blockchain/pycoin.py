from pathlib import Path

from pycoin.blockchain.tool_blockchain import (
    initialize_blockchain_file,
    initialize_node_file,
)
from pycoin.settings import Settings
from pycoin.transaction import Transaction

settings = Settings()


class BlockchainInitializer:
    def __init__(self, nodes_file_path: Path = settings.NODES_FILENAME,
                block_file_path: Path = settings.BLOCK_FILENAME,
                transaction_file_path: Path = settings.TRANSACTION_FILENAME):
        # TODO: Inicializar arquivos importantes
        # blochchain
        # transactiosn
        # nodes
        initialize_node_file(nodes_file_path=nodes_file_path)
        initialize_blockchain_file(block_file_path=block_file_path)
        Transaction.initialize_transaction_file(transaction_file_path=transaction_file_path)
        # load_chain(settings.NODES_FILENAME)
        # replace_chain()
