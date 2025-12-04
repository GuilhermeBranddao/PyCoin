import os
import shutil
import sys

# --- Configuração de Path ---
# Adiciona o diretório raiz do projeto ao PYTHONPATH para conseguir importar 'core' e 'node'
# Isso permite rodar o script de qualquer lugar
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.block import Block
from node.storage.chain_repository import ChainRepository


def initialize(force: bool = False, node_folder: str = None):
    print("🚀 Inicializando PyCoin Blockchain...")

    # Define o caminho base: usa node_folder se fornecido, senão usa "./data"
    if node_folder:
        base_path = node_folder
        print(f"📁 Usando pasta personalizada: {base_path}")
    else:
        base_path = "./data"
        print(f"📁 Usando pasta padrão: {base_path}")

    # Caminhos padrão (mesmos do ChainRepository)
    DB_PATH = os.path.join(base_path, "chainstate")
    BLOCKS_PATH = os.path.join(base_path, "blocks")

    # Se a flag force for usada, apaga tudo e recomeça (CUIDADO!)
    if force and os.path.exists(base_path):
        print("⚠️  Modo FORCE detectado. Apagando dados antigos...")
        shutil.rmtree(base_path)

    # 1. Instancia o Repositório com os caminhos customizados
    # Ele criará as pastas automaticamente
    repo = ChainRepository(db_path=DB_PATH, blocks_path=BLOCKS_PATH)

    try:
        # 2. Verifica se a chain já tem vida
        last_hash = repo.get_last_block_hash()
        if last_hash:
            print(f"⚠️  A Blockchain já existe! Tip: {last_hash[:10]}...")
            print("❌  Aborting. Use 'force=True' se quiser resetar (perda de dados).")
            return

        # 3. Cria o Bloco Gênesis (Hardcoded no core/block.py)
        print("🔨 Forjando o Bloco Gênesis...")
        genesis_block = Block.create_genesis_block()

        # 4. Salva no Storage (LevelDB + Flat File)
        repo.save_block(genesis_block)

        print("-" * 40)
        print("✅  Gênesis salvo com sucesso!")
        print(f"🔑  Hash:   {genesis_block.id}")
        print(f"📦  Height: {genesis_block.height}")
        print(f"📅  Time:   {genesis_block.header.timestamp}")
        print(f"💾  Local:  {os.path.abspath(BLOCKS_PATH)}")
        print("-" * 40)
        print("💡 Próximo passo: Inicie o servidor com 'python node/app.py' (ou uvicorn)")

    finally:
        # Sempre fechar o banco para evitar corrupção de lock
        repo.close()


if __name__ == "__main__":
    # Permite rodar com:
    # - python scripts/init_blockchain.py
    # - python scripts/init_blockchain.py --force
    # - python scripts/init_blockchain.py --port 8000
    # - python scripts/init_blockchain.py --port 8001 --force
    # - python scripts/init_blockchain.py --folder ./data/node_8000
    # - python scripts/init_blockchain.py --folder ./data/node_8000 --force

    force_mode = "--force" in sys.argv
    port = None
    node_folder = None

    # Parse argumentos
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--port" and i < len(sys.argv) - 1:
            try:
                port = int(sys.argv[i + 1])
                node_folder = f"./data/node_{port}"
            except (ValueError, IndexError):
                print("❌ Erro: --port requer um número de porta válido")
                sys.exit(1)
        elif arg == "--folder" and i < len(sys.argv) - 1:
            node_folder = sys.argv[i + 1]

    if port:
        print(f"🔌 Port: {port} → Pasta: {node_folder}")

    initialize(force=force_mode, node_folder=node_folder)
