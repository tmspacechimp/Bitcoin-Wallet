from dataclasses import dataclass, field
from hashlib import sha256
from typing import Callable, Optional

from app.core.constants.constants import ADMIN_KEY, INITIAL_BALANCE, KEY_FOR_ADDRESS_GEN
from app.core.interactors.authentication import (
    AuthenticateInteractor,
    IAuthenticateInteractor,
)
from app.core.interactors.commission import CommissionCalculator, ICommissionCalculator
from app.core.interactors.transactions import (
    ITransactionsInteractor,
    ITransactionsRepository,
    TransactionsInteractor,
)
from app.core.interactors.users import (
    IUsersInteractor,
    IUsersRepository,
    UserInteractor,
)
from app.core.interactors.wallets import (
    IWalletsInteractor,
    IWalletsRepository,
    WalletsInteractor,
)
from app.core.models.req.transaction import TransactionRequest
from app.core.models.req.user import CreateUserRequest
from app.core.models.resp.core_response import CoreResponse, CoreStatus
from app.core.models.resp.statistics import BadStatisticsResponse, StatisticsResponse
from app.core.models.resp.transaction import GetTransactionsResponse
from app.core.models.resp.user import CreateUserResponse
from app.core.models.resp.wallet import BadWalletResponse, WalletResponse


def sha_256_using_hardcoded_key(user_id: int, wallet_address: int) -> str:
    return sha256(
        f"{user_id}-{wallet_address}-{KEY_FOR_ADDRESS_GEN}".encode()
    ).hexdigest()


@dataclass
class BitcoinWalletCore:
    transactions_interactor: ITransactionsInteractor
    user_interactor: IUsersInteractor
    wallet_interactor: IWalletsInteractor
    authenticate_interactor: IAuthenticateInteractor
    commission_calculator: ICommissionCalculator
    address_generation_strategy: Callable[[int, int], str] = field(
        default=sha_256_using_hardcoded_key
    )

    def create_user(
        self, request: CreateUserRequest
    ) -> CoreResponse[CreateUserResponse]:
        return self.user_interactor.create_user(request)

    def make_transaction(
        self, api_key: Optional[str], req: TransactionRequest
    ) -> CoreResponse[None]:
        # check if api key is valid
        user_id_response = self.user_interactor.get_user_id(api_key)
        if user_id_response.status != CoreStatus.SUCCESSFUL_GET:
            return self._create_bad_none_response(
                user_id_response.status, user_id_response.message
            )

        # get wallet_ids for addresses
        from_id_response = self.wallet_interactor.get_wallet_id(req.from_address)

        # check address belongs to user
        check_ownership_response = self.wallet_interactor.check_wallet_belongs_to_user(
            from_id_response.response_content, user_id_response.response_content
        )
        if check_ownership_response.status == CoreStatus.WALLET_DOESNT_BELONG_TO_USER:
            return self._create_bad_none_response(
                check_ownership_response.status, check_ownership_response.message
            )

        # check sending wallet exist
        to_id_response = self.wallet_interactor.check_wallet_exists(req.to_address)
        if to_id_response.status != CoreStatus.SUCCESSFUL_GET:
            return self._create_bad_none_response(
                to_id_response.status, to_id_response.message
            )

        # calculate commission
        commission = self.commission_calculator.get_commission(
            user_id_response.response_content,
            from_id_response.response_content,
            to_id_response.response_content,
            req.amount_in_satoshi,
        )

        # check wallet has enough balance
        balance = self.wallet_interactor.get_wallet_balance(
            req.from_address
        ).response_content.satoshi_balance
        if balance < req.amount_in_satoshi + commission:
            return self._create_bad_none_response(
                CoreStatus.INSUFFICIENT_FUNDS, "insufficient funds"
            )

        # update balance if transaction successful
        transaction_response = self.transactions_interactor.create(
            from_id_response.response_content,
            to_id_response.response_content,
            req.amount_in_satoshi,
            commission,
        )
        if transaction_response.status != CoreStatus.SUCCESSFUL_POST:
            return transaction_response

        self.wallet_interactor.update_balance(
            req.from_address, balance - (req.amount_in_satoshi + commission)
        )
        receiver_balance = balance = self.wallet_interactor.get_wallet_balance(
            req.to_address
        ).response_content.satoshi_balance
        self.wallet_interactor.update_balance(
            req.to_address, receiver_balance + req.amount_in_satoshi
        )
        transaction_response.message = "Transaction completed successfully"
        return transaction_response

    def get_transactions(
        self, api_key: Optional[str]
    ) -> CoreResponse[GetTransactionsResponse]:
        # check if api key is valid
        user_id_response = self.user_interactor.get_user_id(api_key)
        if user_id_response.status != CoreStatus.SUCCESSFUL_GET:
            return self._create_bad_transactions_response(
                user_id_response.status, user_id_response.message
            )

        # get wallet_ids for user (always: SUCCESSFUL_GET)
        wallet_ids_response = self.wallet_interactor.get_user_wallets(
            user_id_response.response_content
        )

        # get transactions for wallet_ids
        return self.transactions_interactor.get(wallet_ids_response.response_content)

    def get_transactions_for_wallet(
        self, api_key: Optional[str], address: str
    ) -> CoreResponse[GetTransactionsResponse]:
        # check if api key is valid
        user_id_response = self.user_interactor.get_user_id(api_key)
        if user_id_response.status != CoreStatus.SUCCESSFUL_GET:
            return self._create_bad_transactions_response(
                user_id_response.status, user_id_response.message
            )

        # get wallet_id for address
        wallet_id_response = self.wallet_interactor.get_wallet_id(address)
        if wallet_id_response.status != CoreStatus.SUCCESSFUL_GET:
            return self._create_bad_transactions_response(
                wallet_id_response.status, wallet_id_response.message
            )

        # check if address is owned by the user
        check_ownership_response = self.wallet_interactor.check_wallet_belongs_to_user(
            wallet_id_response.response_content, user_id_response.response_content
        )
        if not check_ownership_response.response_content:
            return self._create_bad_transactions_response(
                check_ownership_response.status, check_ownership_response.message
            )

        # get transactions for wallet_id
        return self.transactions_interactor.get([wallet_id_response.response_content])

    def create_wallet(self, api_key: str | None) -> CoreResponse[WalletResponse]:
        user_id_response = self.user_interactor.get_user_id(api_key)
        if user_id_response.status != CoreStatus.SUCCESSFUL_GET:
            return self._create_bad_wallet_response(
                user_id_response.status, user_id_response.message
            )

        wallets = self.wallet_interactor.get_user_wallets(
            user_id_response.response_content
        ).response_content
        address = self.address_generation_strategy(
            user_id_response.response_content, len(wallets)
        )
        # create wallet
        return self.wallet_interactor.create_wallet(
            user_id_response.response_content,
            address,
            INITIAL_BALANCE,
        )

    def get_wallet_balance(
        self, api_key: Optional[str], address: str
    ) -> CoreResponse[WalletResponse]:
        # check if api key is valid
        user_id_response = self.user_interactor.get_user_id(api_key)
        if user_id_response.status != CoreStatus.SUCCESSFUL_GET:
            return self._create_bad_wallet_response(
                user_id_response.status, user_id_response.message
            )
        # get wallet_ids for addresses
        wallet_id_response = self.wallet_interactor.get_wallet_id(address)

        # check address belongs to user
        check_ownership_response = self.wallet_interactor.check_wallet_belongs_to_user(
            wallet_id_response.response_content, user_id_response.response_content
        )
        if check_ownership_response.status == CoreStatus.WALLET_DOESNT_BELONG_TO_USER:
            return self._create_bad_wallet_response(
                check_ownership_response.status, check_ownership_response.message
            )
        return self.wallet_interactor.get_wallet_balance(address)

    def get_statistics(
        self, admin_key: Optional[str]
    ) -> CoreResponse[StatisticsResponse]:
        if not self.authenticate_interactor.authenticate(admin_key):
            return CoreResponse(
                BadStatisticsResponse, CoreStatus.INVALID_ADMIN_KEY, "invalid admin key"
            )
        return self.transactions_interactor.get_statistics()

    @classmethod
    def create(
        cls,
        transactions_repository: ITransactionsRepository,
        users_repository: IUsersRepository,
        wallets_repository: IWalletsRepository,
    ) -> "BitcoinWalletCore":
        return cls(
            transactions_interactor=TransactionsInteractor(
                transaction_repository=transactions_repository
            ),
            user_interactor=UserInteractor(user_repository=users_repository),
            wallet_interactor=WalletsInteractor(wallet_repository=wallets_repository),
            commission_calculator=CommissionCalculator(
                wallet_repository=wallets_repository
            ),
            authenticate_interactor=AuthenticateInteractor(
                authentication_key=ADMIN_KEY
            ),
        )

    @classmethod
    def _create_bad_wallet_response(
        cls, status: CoreStatus, message: str
    ) -> CoreResponse[WalletResponse]:
        return CoreResponse(
            response_content=BadWalletResponse, status=status, message=message
        )

    @classmethod
    def _create_bad_transactions_response(
        cls, status: CoreStatus, message: str
    ) -> CoreResponse[GetTransactionsResponse]:
        return CoreResponse(
            response_content=GetTransactionsResponse([]),
            status=status,
            message=message,
        )

    @classmethod
    def _create_bad_none_response(
        cls, status: CoreStatus, message: str
    ) -> CoreResponse[None]:
        return CoreResponse(
            response_content=None,
            status=status,
            message=message,
        )
