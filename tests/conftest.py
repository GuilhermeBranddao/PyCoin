import pytest
from fastapi.testclient import TestClient

from pycoin.app import app
from pycoin.blockchain.pycoin import BlockchainInitializer
from pycoin.settings import Settings

settings = Settings()
BlockchainInitializer(
    nodes_file_path=settings.TEST_NODES_FILENAME,
    block_file_path=settings.TEST_BLOCK_FILENAME,
    transaction_file_path=settings.TEST_TRANSACTION_FILENAME,
)


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client
