from typing import List

from pydantic import BaseModel, Field


class AddTransaction(BaseModel):
    private_key_sender: str
    public_key_sender: str
    recipient_address: str
    amount: float


# Modelo de dados para um nó (endereço e porta)
class Node(BaseModel):
    node_address: str = Field(..., example="127.0.0.1")
    port: int = Field(..., example=8001)


# Modelo para a requisição que contém uma lista de nós
class NodeListRequest(BaseModel):
    nodes: List[Node] = Field(
        ...,
        example=[  # Exemplo de uma lista de nós
            {"node_address": "127.0.0.1", "port": 8001},
            {"node_address": "192.168.0.1", "port": 8002}
        ]
    )


class BalanceRequest(BaseModel):
    address: str = Field(...,
        example="w3XKxU9J2deUzYgsFx5YTsZZg3Q="
    )
