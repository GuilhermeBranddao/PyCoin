from pycoin.blockchain.block_utils import (
    create_genesis_block,
    get_previous_block,
)
from pycoin.settings.config import Settings

settings = Settings()


def test_create_genesis_block():
    list_genesis_block = create_genesis_block()
    dict_genesis_block = list_genesis_block[0]
    list_keys = ['index', 'timestamp', 'proof',
                 'hash', 'previous_hash', 'transactions']

    assert all([key in list_keys for key in dict_genesis_block])


def test_get_previous_block():
    chain = get_previous_block(settings.TEST_BLOCKCHAIN_FILE)
    list_keys = ['index', 'timestamp', 'proof',
                 'hash', 'previous_hash', 'transactions']

    print([key in list_keys for key in chain])

    assert all([key in list_keys for key in chain])


# task test tests/test_tools_blockchain.py::test_create_genesis_block
