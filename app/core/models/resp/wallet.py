from dataclasses import dataclass
from decimal import Decimal


@dataclass
class WalletResponse:
    address: str
    satoshi_balance: int
    usd_balance: Decimal


# not meant to be read, just a placeholder to avoid using optionals
BadWalletResponse = WalletResponse("", 0, Decimal(0))
