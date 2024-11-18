from pydantic import BaseModel

class AddTransaction(BaseModel):
    private_key_sender: str
    public_key_sender: str
    recipient_address: str
    amount: float