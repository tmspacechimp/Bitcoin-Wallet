from dataclasses import dataclass
from typing import List


@dataclass
class TransactionResponse:
    from_address: str
    to_address: str
    amount_in_satoshi: int


@dataclass
class GetTransactionsResponse:
    transactions: List[TransactionResponse]
