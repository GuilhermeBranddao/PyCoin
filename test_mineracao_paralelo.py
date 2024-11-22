import asyncio

# Variável de controle global
is_mining = True

# Função do minerador
async def miner():
    global is_mining
    while is_mining:
        print("Minerando um bloco...")
        await asyncio.sleep(5)  # Simula o tempo de mineração
        print("Bloco minerado e propagado!")

# Função para iniciar o minerador como uma tarefa no event loop
async def start_miner():
    # Inicia a mineração como uma tarefa assíncrona
    asyncio.create_task(miner())

# Função para parar o minerador
async def shutdown_event():
    global is_mining
    print("Aguardando para parar o minerador...")
    await asyncio.sleep(3)  # Simula o tempo antes de desligar
    is_mining = False
    print("Minerador foi parado.")

# Função principal
async def main():
    # Inicia o minerador
    await start_miner()

    # Simula o desligamento após 15 segundos
    await asyncio.sleep(15)
    await shutdown_event()

# Inicializa o event loop
if __name__ == "__main__":
    asyncio.run(main())
