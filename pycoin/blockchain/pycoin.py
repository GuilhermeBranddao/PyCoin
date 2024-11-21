from pycoin.blockchain.tool_blockchain import (
    load_chain,
    load_nodes,
    replace_chain,
)
from pycoin.settings import Settings

settings = Settings()


class BlockchainInitializer:
    def __init__(self):
        load_nodes(settings.BLOCK_FILENAME)
        load_chain(settings.NODES_FILENAME)
        replace_chain()
