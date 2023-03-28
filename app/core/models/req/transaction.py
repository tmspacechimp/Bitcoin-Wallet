from pydantic import BaseModel


class TransactionRequest(BaseModel):
    from_address: str
    to_address: str
    amount_in_satoshi: int
