from dataclasses import dataclass
from typing import List, Protocol, Tuple

from app.core.models.resp.core_response import CoreResponse, CoreStatus
from app.core.models.resp.statistics import StatisticsResponse
from app.core.models.resp.transaction import (
    GetTransactionsResponse,
    TransactionResponse,
)


class ITransactionsRepository(Protocol):
    def check_transaction_validity(self, from_id: int, to_id: int) -> bool:
        pass

    def create_transaction(
        self, from_id: int, to_id: int, amount: int, commission_satoshi: int
    ) -> bool:
        pass

    def get_transactions(self, wallet_ids: List[int]) -> List[TransactionResponse]:
        pass

    def get_statistics(self) -> Tuple[int, int]:
        pass


class ITransactionsInteractor(Protocol):
    def create(
        self, from_id: int, to_id: int, amount: int, commission_satoshi: int
    ) -> CoreResponse[None]:
        pass

    def get(self, wallet_ids: List[int]) -> CoreResponse[GetTransactionsResponse]:
        pass

    def get_statistics(self) -> CoreResponse[StatisticsResponse]:
        pass


DEFAULT_MESSAGE = "empty message body"


@dataclass
class TransactionsInteractor:
    transaction_repository: ITransactionsRepository
    tag = "transactions"

    def create(
        self, from_id: int, to_id: int, amount: int, commission_satoshi: int
    ) -> CoreResponse[None]:
        # response_status = self.transaction_repository.check_transaction_validity(
        #     from_id=from_id, to_id=to_id
        # )
        # if response_status:
        response_status = self.transaction_repository.create_transaction(
            from_id=from_id,
            to_id=to_id,
            amount=amount,
            commission_satoshi=commission_satoshi,
        )
        response: CoreResponse[None] = CoreResponse(None)
        response.status = (
            CoreStatus.SUCCESSFUL_POST
            if response_status
            else CoreStatus.UNSUCCESSFUL_POST
        )
        response.message = f"{self.tag} {DEFAULT_MESSAGE}"
        return response

    def get(self, wallet_ids: List[int]) -> CoreResponse[GetTransactionsResponse]:
        my_transactions: List[
            TransactionResponse
        ] = self.transaction_repository.get_transactions(wallet_ids=wallet_ids)
        response: CoreResponse[GetTransactionsResponse] = CoreResponse(
            GetTransactionsResponse(my_transactions)
        )
        response.status = CoreStatus.SUCCESSFUL_GET
        response.message = f"{self.tag} {DEFAULT_MESSAGE}"
        return response

    def get_statistics(self) -> CoreResponse[StatisticsResponse]:
        total_count, profit = self.transaction_repository.get_statistics()
        response: CoreResponse[StatisticsResponse] = CoreResponse(
            response_content=StatisticsResponse(total_count, profit),
            status=CoreStatus.SUCCESSFUL_GET,
            message="Success",
        )
        return response
