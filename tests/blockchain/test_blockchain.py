

import datetime

from pycoin.blockchain.block_utils import (
    calculate_hash,
    get_previous_block,
    load_chain,
    proof_of_work,
    save_blockchain,
)
from pycoin.settings.config import Settings
from pycoin.transaction import Transaction

transaction = Transaction()
settings = Settings()


async def test_start_block_mining():

    previous_block = get_previous_block()
    proof = await proof_of_work(previous_proof=previous_block['proof'], is_sleep=False)

    chain = load_chain(block_file_path=settings.TEST_BLOCKCHAIN_FILE)

    transaction.add_transaction_miner_reward(
            miner_address=settings.TEST_MINER_PUBLIC_ADDRESS,
            reward_amount=settings.MINING_REWARD)

    block = {
            'index': len(chain),
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'hash': calculate_hash(previous_block),
            'previous_hash': previous_block['hash'],
            'transactions': transaction.load_transactions(transaction.transactions_file_path),
        }

    assert transaction.clear_transactions(transaction.transactions_file_path)

    chain.append(block)

    assert save_blockchain(block_file_path=settings.TEST_BLOCKCHAIN_FILE,
                        blockchain=chain)


async def test_check_transaction_miner():
    previous_block = await get_previous_block(
        block_file_path=settings.TEST_BLOCKCHAIN_FILE)

    has_assress_miner_transaction = any([transaction['recipient_address'] == settings.TEST_MINER_PUBLIC_ADDRESS
                                          for transaction in previous_block['transactions']])

    assert has_assress_miner_transaction
