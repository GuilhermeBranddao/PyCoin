import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    # Caminhos para os arquivos JSON
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR: Path = os.path.join(BASE_DIR, "../data")
    BLOCKCHAIN_FILE: Path = os.path.join(DATA_DIR, "blockchain/block.json")
    NODES_FILE: Path = os.path.join(DATA_DIR, "nodes/nodes.json")
    TRANSACTIONS_FILE: Path = os.path.join(DATA_DIR, "transactions/transactions.json")

    TEST_BLOCKCHAIN_FILE: Path = os.path.join(DATA_DIR, "blockchain/test_block.json")
    TEST_NODES_FILE: Path = os.path.join(DATA_DIR, "nodes/test_nodes.json")
    TEST_TRANSACTIONS_FILE: Path = os.path.join(DATA_DIR, "transactions/test_transactions.json")

    TEST_MINER_PRIVATE_KEY: str = "MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgWthL3MwWXCBxlpJWMFnntZNbfEo+tKzhPZ2ov+6pzpehRANCAASmRLYK8qkM57uTA4DR+a+krTHgSDNQttGsm7RHz72t47Ykgfb3xCfEAZZZSThvvsQY4HDRJf56zjfRhjGCxMp1"
    TEST_MINER_PUBLIC_KEY: str = "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEpkS2CvKpDOe7kwOA0fmvpK0x4EgzULbRrJu0R8+9reO2JIH298QnxAGWWUk4b77EGOBw0SX+es430YYxgsTKdQ=="
    TEST_MINER_PUBLIC_ADDRESS: str = "p2SbWoT9K0gJQf78leNZ1AgXjU0="

    LIST_NODE_VALID: str

    MINER_PRIVATE_KEY: str
    MINER_PUBLIC_KEY: str
    MINER_PUBLIC_ADDRESS: str
    MINING_REWARD: float

    # Configurações gerais
    APP_NAME: str = "PyCoin"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Configurações de rede
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    MY_NODE: str

    # Configurações de mineração
    MINING_DIFFICULTY: int = 4
    REWARD: float = 50.0

    # Para garantir que a string será convertida em uma lista
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if isinstance(self.LIST_NODE_VALID, str):
            self.LIST_NODE_VALID = self.LIST_NODE_VALID.split(',')
