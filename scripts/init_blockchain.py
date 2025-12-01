import sys
import os
import shutil

# --- Configuração de Path ---
# Adiciona o diretório raiz do projeto ao PYTHONPATH para conseguir importar 'core' e 'node'
# Isso permite rodar o script de qualquer lugar
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.block import Block
from node.storage.chain_repository import ChainRepository

def initialize(force: bool = False):
    print("🚀 Inicializando PyCoin Blockchain...")
    
    # Caminhos padrão (mesmos do ChainRepository)
    DB_PATH = "./data/chainstate"
    BLOCKS_PATH = "./data/blocks"

    # Se a flag force for usada, apaga tudo e recomeça (CUIDADO!)
    if force and os.path.exists("./data"):
        print("⚠️  Modo FORCE detectado. Apagando dados antigos...")
        shutil.rmtree("./data")

    # 1. Instancia o Repositório
    # Ele criará as pastas ./data/chainstate e ./data/blocks automaticamente
    repo = ChainRepository()

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
        print(f"✅  Gênesis salvo com sucesso!")
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
    # Permite rodar com `python scripts/init_blockchain.py --force`
    force_mode = "--force" in sys.argv
    initialize(force=force_mode)