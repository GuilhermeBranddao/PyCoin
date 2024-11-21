from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    NODES_FILENAME: Path
    LIST_NODE_VALID: str
    BLOCK_FILENAME: Path
    MY_NODE: str
    TRANSACTION_FILENAME: Path

    MINER_PRIVATE_KEY: str
    MINER_PUBLIC_KEY: str
    MINER_PUBLIC_ADDRESS: str
    MINING_REWARD: float

    TEST_NODES_FILENAME: Path
    TEST_BLOCK_FILENAME: Path
    TEST_TRANSACTION_FILENAME: Path

    TEST_MINER_PRIVATE_KEY: str
    TEST_MINER_PUBLIC_KEY: str
    TEST_MINER_PUBLIC_ADDRESS: str

    # Para garantir que a string será convertida em uma lista
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if isinstance(self.LIST_NODE_VALID, str):
            self.LIST_NODE_VALID = self.LIST_NODE_VALID.split(',')
