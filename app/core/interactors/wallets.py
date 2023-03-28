from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Protocol

from app.core.constants.constants import WALLET_LIMIT_PER_USER
from app.core.interactors.conversion import (
    Currency,
    IRateService,
    SubstitutableHTTPRateService,
)
from app.core.models.resp.core_response import CoreResponse, CoreStatus
from app.core.models.resp.wallet import BadWalletResponse, WalletResponse


class IWalletsRepository(Protocol):
    def create_wallet(self, user_id: int, address: str, init_balance: int) -> bool:
        pass

    def get_wallet_id(self, address: str) -> int:
        pass

    def get_user_wallets(self, user_id: int) -> List[int]:
        pass

    def check_wallet_validity(self, wallet_address: str) -> int:
        pass

    def get_wallet_balance(self, address: str) -> int:
        pass

    def set_balance(self, address: str, amount: int) -> bool:
        pass


class IWalletsInteractor(Protocol):
    def create_wallet(
        self, user_id: int, address: str, init_balance: int
    ) -> CoreResponse[WalletResponse]:
        pass

    def get_wallet_id(self, address: str) -> CoreResponse[int]:
        pass

    def get_user_wallets(self, user_id: int) -> CoreResponse[List[int]]:
        pass

    def check_wallet_exists(self, address: str) -> CoreResponse[int]:
        pass

    def get_wallet_balance(self, address: str) -> CoreResponse[WalletResponse]:
        pass

    def check_wallet_belongs_to_user(
        self, wallet_id: int, user_id: int
    ) -> CoreResponse[bool]:
        pass

    def update_balance(self, address: str, amount: int) -> CoreResponse[None]:
        pass


class BitcoinToUsdConverter(Protocol):
    def convert_to_usd(self, bitcoin: Decimal) -> Decimal:
        pass


@dataclass
class HTTPConverter(BitcoinToUsdConverter):
    rate_service: IRateService = field(default=SubstitutableHTTPRateService())

    def convert_to_usd(self, bitcoin: Decimal) -> Decimal:
        converted = Decimal(
            Decimal(
                self.rate_service.get_rate(Currency.BITCOIN, Currency.USD) * bitcoin
            )
        )
        return converted.quantize(Decimal("0.01"))


@dataclass
class WalletsInteractor:
    wallet_repository: IWalletsRepository
    converter: BitcoinToUsdConverter = field(default_factory=HTTPConverter)

    def create_wallet(
        self, user_id: int, address: str, init_balance: int
    ) -> CoreResponse[WalletResponse]:
        wallets = self.get_user_wallets(user_id).response_content

        if len(wallets) >= WALLET_LIMIT_PER_USER:
            return CoreResponse(
                response_content=BadWalletResponse,
                status=CoreStatus.WALLET_LIMIT_REACHED,
                message=f"can't have more than {WALLET_LIMIT_PER_USER} wallets",
            )

        created = self.wallet_repository.create_wallet(user_id, address, init_balance)

        if not created:
            return CoreResponse(
                response_content=BadWalletResponse,
                status=CoreStatus.WALLET_ADDRESS_TAKEN,
                message=f"wallet address {address} already taken",
            )

        return CoreResponse(
            response_content=WalletResponse(
                address,
                init_balance,
                self.converter.convert_to_usd(Decimal(init_balance / 100000000)),
            ),
            status=CoreStatus.SUCCESSFUL_POST,
            message=f"created wallet {address}",
        )

    def get_wallet_id(self, address: str) -> CoreResponse[int]:
        wallet_id = self.wallet_repository.get_wallet_id(address)

        if wallet_id == -1:
            return CoreResponse(
                response_content=wallet_id,
                status=CoreStatus.INVALID_REQUEST,
                message=f"wallet address: {address} doesn't exist",
            )

        return CoreResponse(
            response_content=wallet_id,
            status=CoreStatus.SUCCESSFUL_GET,
            message=f"got id for address: {address}",
        )

    def get_user_wallets(self, user_id: int) -> CoreResponse[List[int]]:
        ids = self.wallet_repository.get_user_wallets(user_id)

        return CoreResponse(
            response_content=ids,
            status=CoreStatus.SUCCESSFUL_GET,
            message=f"got wallets for user: {user_id}",
        )

    def check_wallet_exists(self, address: str) -> CoreResponse[int]:
        valid = self.wallet_repository.check_wallet_validity(address)

        if valid < 0:
            return CoreResponse(
                response_content=valid,
                status=CoreStatus.INVALID_REQUEST,
                message=f"wallet address: {address} invalid",
            )

        return CoreResponse(
            response_content=valid,
            status=CoreStatus.SUCCESSFUL_GET,
            message=f"wallet address: {address} valid",
        )

    def get_wallet_balance(self, address: str) -> CoreResponse[WalletResponse]:
        valid = self.wallet_repository.check_wallet_validity(address)

        if valid < 0:
            return CoreResponse(
                response_content=BadWalletResponse,
                status=CoreStatus.INVALID_REQUEST,
                message=f"wallet address: {address} invalid",
            )

        satoshi_balance = self.wallet_repository.get_wallet_balance(address)
        usd_balance = self.converter.convert_to_usd(
            Decimal(satoshi_balance / 100000000)
        )
        return CoreResponse(
            response_content=WalletResponse(address, satoshi_balance, usd_balance),
            status=CoreStatus.SUCCESSFUL_GET,
            message=f"successfully retrieved balance for address: {address}",
        )

    def check_wallet_belongs_to_user(
        self, wallet_id: int, user_id: int
    ) -> CoreResponse[bool]:
        wallet_ids = self.wallet_repository.get_user_wallets(user_id)
        if wallet_id not in wallet_ids:
            return CoreResponse(
                response_content=False,
                status=CoreStatus.WALLET_DOESNT_BELONG_TO_USER,
                message=(
                    "Wallet with that address does not exist"
                    if wallet_id == -1
                    else "Wallet does not belong to user"
                ),
            )

        return CoreResponse(
            response_content=True,
            status=CoreStatus.SUCCESSFUL_GET,
            message="Wallet belongs to user",
        )

    def update_balance(self, address: str, amount: int) -> CoreResponse[None]:
        self.wallet_repository.set_balance(address, amount)
        return CoreResponse(
            response_content=None,
            status=CoreStatus.SUCCESSFUL_POST,
            message=f"balance for wallet: {address} updated to {amount}",
        )
