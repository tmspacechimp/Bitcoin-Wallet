from dataclasses import dataclass
from math import ceil
from typing import Protocol

from app.core.constants.constants import COMMISSION_PERCENT
from app.core.interactors.wallets import IWalletsRepository


class ICommissionCalculator(Protocol):
    def get_commission(
        self, user_id: int, from_id: int, to_id: int, amount: int
    ) -> int:
        pass


@dataclass
class CommissionCalculator:
    wallet_repository: IWalletsRepository

    def get_commission(
        self, user_id: int, from_id: int, to_id: int, amount: int
    ) -> int:
        wallet_ids = self.wallet_repository.get_user_wallets(user_id)
        if from_id in wallet_ids and to_id in wallet_ids:
            return 0
        return int(ceil(amount * COMMISSION_PERCENT / 100))
