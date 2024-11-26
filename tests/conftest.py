import pytest
from fastapi.testclient import TestClient

from pycoin.app import app
from pycoin.blockchain.blockchain_manager import BlockchainInitializer
from pycoin.settings.settings import Settings

settings = Settings()
BlockchainInitializer(
    nodes_file_path=settings.TEST_NODES_FILE,
    block_file_path=settings.TEST_BLOCKCHAIN_FILE,
    transaction_file_path=settings.TEST_TRANSACTIONS_FILE,
)


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client
