

import datetime

from pycoin.blockchain.tool_blockchain import (
    calculate_hash,
    get_previous_block,
    load_chain,
    proof_of_work,
    save_blockchain,
)
from pycoin.settings import Settings
from pycoin.transaction import Transaction

transaction = Transaction()
settings = Settings()


def test_create_block():

    previous_block = get_previous_block()
    chain = load_chain(block_file_path=settings.TEST_BLOCK_FILENAME)

    transaction.add_transaction_miner_reward(
            miner_address=settings.TEST_MINER_PUBLIC_ADDRESS,
            reward_amount=settings.MINING_REWARD)

    block = {
            'index': len(chain),
            'timestamp': str(datetime.datetime.now()),
            'proof': proof_of_work(previous_proof=previous_block['proof']),
            'hash': calculate_hash(previous_block),
            'previous_hash': previous_block['hash'],
            'transactions': transaction.load_transactions(transaction.transactions_file_path),
        }

    assert transaction.clear_transactions(transaction.transactions_file_path)

    chain.append(block)

    assert save_blockchain(block_file_path=settings.TEST_BLOCK_FILENAME,
                        blockchain=chain)


def test_check_transaction_miner():
    previous_block = get_previous_block(
        block_file_path=settings.TEST_BLOCK_FILENAME)

    has_assress_miner_transaction = any([transaction['recipient_address'] == settings.TEST_MINER_PUBLIC_ADDRESS
                                          for transaction in previous_block['transactions']])

    assert has_assress_miner_transaction
