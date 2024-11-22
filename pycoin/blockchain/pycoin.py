from pycoin.blockchain.tool_blockchain import (
    initialize_blockchain_file,
    initialize_node_file,
)
from pycoin.settings import Settings
from pycoin.transaction import Transaction

settings = Settings()


class BlockchainInitializer:
    def __init__(self):
        # TODO: Inicializar arquivos importantes
        # blochchain
        # transactiosn
        # nodes
        initialize_node_file()
        initialize_blockchain_file()
        Transaction.initialize_transaction_file()
        # load_chain(settings.NODES_FILENAME)
        # replace_chain()
