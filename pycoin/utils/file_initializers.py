import json
from pathlib import Path
from typing import Callable, Optional

from pycoin.blockchain.block_utils import (
    create_genesis_block,
    save_blockchain,
    save_nodes,
    update_blockchain,
)
from pycoin.settings.config import Settings

settings = Settings()


def initialize_file(
    file_path: Path,
    init_callback: Optional[Callable[[Path], None]] = None,
    update_callback: Optional[Callable[[], None]] = None
) -> bool:
    """
    Inicializa um arquivo genérico, criando-o e executando callbacks de inicialização e atualização.

    :param file_path: Caminho do arquivo a ser inicializado.
    :param init_callback: Função opcional para inicializar o conteúdo do arquivo caso ele não exista.
    :param update_callback: Função opcional para atualizar o arquivo ou estado relacionado.
    :return: True se a operação foi bem-sucedida.
    """

    if not isinstance(file_path, Path):
        raise ValueError(f"O parâmetro file_path deve ser um objeto do tipo Path. Recebido: {type(file_path)}")

    is_file_exists = file_path.exists()

    if is_file_exists:
        print(f"Arquivo: {file_path} já inicializando")
        return True

    print(f"Inicializando arquivo: {file_path}")

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.touch()

    if not is_file_exists and init_callback:
        init_callback(file_path)

    if update_callback:
        update_callback()

    return True


def initialize_blockchain_file(block_file_path: Path = settings.BLOCKCHAIN_FILE) -> bool:
    def init_blockchain(file_path: Path):
        print("Gerando bloco genesis")
        blockchain = create_genesis_block()
        save_blockchain(block_file_path=file_path, blockchain=blockchain)

    return initialize_file(
        file_path=block_file_path,
        init_callback=init_blockchain,
        update_callback=update_blockchain
    )


def initialize_node_file(nodes_file_path: Path = settings.NODES_FILE) -> bool:
    def init_nodes(file_path: Path):
        save_nodes(nodes_file_path=file_path, list_new_nodes=settings.LIST_NODE_VALID)

    return initialize_file(file_path=nodes_file_path, init_callback=init_nodes)


def initialize_transaction_file(transaction_file_path: Path = settings.TRANSACTIONS_FILE) -> bool:
    def init_transactions(file_path: Path):
        transactions = {"transactions": []}
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(transactions, file, indent=4)

    return initialize_file(file_path=transaction_file_path, init_callback=init_transactions)
