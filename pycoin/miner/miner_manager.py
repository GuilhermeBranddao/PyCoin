import asyncio

class MinerManager:
    def __init__(self):
        self.is_mining = False
        self.miner_task = None

    async def start_mining(self, mine_function):
        if self.is_mining:
            return {"message": "Mineração já está em andamento!"}
        
        self.is_mining = True
        self.miner_task = asyncio.create_task(self._mining_loop(mine_function))
        return {"message": "Mineração iniciada!"}

    async def stop_mining(self):
        if not self.is_mining:
            return {"message": "Nenhuma mineração em andamento para parar!"}
        
        self.is_mining = False
        if self.miner_task:
            await self.miner_task
            self.miner_task = None
        return {"message": "Mineração parada!"}

    async def _mining_loop(self, mine_function):
        while self.is_mining:
            print(">>>>>>Iniciando Mineração<<<<<<")
            result = await mine_function()  # Executa a função de mineração fornecida
            await asyncio.sleep(2)  # Intervalo opcional entre as minerações
            print(f">>>>>>Retomando Mineração {self.is_mining}<<<<<<")
