

from pycoin.blockchain.tool_blockchain import (
    create_genesis_block,
    load_chain,
)
from pycoin.settings import Settings

settings = Settings()


def test_create_genesis_block():
    list_genesis_block = create_genesis_block()
    dict_genesis_block = list_genesis_block[0]
    list_keys = ['index', 'timestamp', 'previous_hash',
                 'hash', 'proof', 'transactions']

    assert all([key in list_keys for key in dict_genesis_block])

def test_load_chain():
    chain = load_chain(settings.TEST_BLOCK_FILENAME)
    list_keys = ['index', 'timestamp', 'previous_hash',
                 'hash', 'proof', 'transactions']

    assert all([key in list_keys for key in chain])



# task test tests/test_tools_blockchain.py::test_create_genesis_block
