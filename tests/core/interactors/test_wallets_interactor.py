from decimal import Decimal
from functools import cache
from sqlite3 import connect

import pytest

from app.core.constants.constants import WALLET_LIMIT_PER_USER
from app.core.interactors.wallets import BitcoinToUsdConverter, WalletsInteractor
from app.core.models.resp.core_response import CoreResponse, CoreStatus
from app.core.models.resp.wallet import BadWalletResponse, WalletResponse
from app.infra.sqlite.users import UsersSqlRepository
from app.infra.sqlite.wallets import WalletsSqlRepository


class MockConverter(BitcoinToUsdConverter):
    def convert_to_usd(self, bitcoin: Decimal) -> Decimal:
        return bitcoin + 1


class TestCreateWallet:
    @classmethod
    @pytest.fixture
    @cache
    def interactor(cls) -> WalletsInteractor:
        # required for wallets_repository to be created
        connection = connect(":memory:", check_same_thread=False)
        users_repository = UsersSqlRepository(connection)
        users_repository.create_user("test", "test_1_key")
        users_repository.create_user("test_2", "test_2_key")

        wallets_repository = WalletsSqlRepository(connection)
        wallets_repository.create_wallet(2, "2_address_1", 100000000)
        wallets_repository.create_wallet(2, "2_address_2", 100000000)
        wallets_repository.create_wallet(2, "2_address_3", 100000000)
        return WalletsInteractor(
            wallet_repository=wallets_repository,
            converter=MockConverter(),
        )

    def test_should_succeed(self, interactor: WalletsInteractor) -> None:
        address = "1_address_1"
        response = interactor.create_wallet(1, address, 100000000)
        assert response == CoreResponse(
            response_content=WalletResponse(address, 100000000, Decimal(2)),
            status=CoreStatus.SUCCESSFUL_POST,
            message=f"created wallet {address}",
        )

    def test_should_fail_wallet_limit_reached(
        self, interactor: WalletsInteractor
    ) -> None:
        address = "2_address_4"
        response = interactor.create_wallet(2, address, 100000000)
        assert response == CoreResponse(
            response_content=BadWalletResponse,
            status=CoreStatus.WALLET_LIMIT_REACHED,
            message=f"can't have more than {WALLET_LIMIT_PER_USER} wallets",
        )

    def test_should_fail_wallet_address_taken(
        self, interactor: WalletsInteractor
    ) -> None:
        address = "2_address_3"
        response = interactor.create_wallet(1, address, 100000000)
        assert response == CoreResponse(
            response_content=BadWalletResponse,
            status=CoreStatus.WALLET_ADDRESS_TAKEN,
            message=f"wallet address {address} already taken",
        )


class TestGetWalletId:
    @classmethod
    @pytest.fixture
    @cache
    def interactor(cls) -> WalletsInteractor:
        # required for wallets_repository to be created
        connection = connect(":memory:", check_same_thread=False)
        users_repository = UsersSqlRepository(connection)
        users_repository.create_user("test_1", "test_1_key")

        wallets_repository = WalletsSqlRepository(connection)
        wallets_repository.create_wallet(1, "1_address_1", 100000000)

        return WalletsInteractor(
            wallet_repository=wallets_repository,
            converter=MockConverter(),
        )

    def test_should_succeed(self, interactor: WalletsInteractor) -> None:
        address = "1_address_1"
        response = interactor.get_wallet_id(address)
        assert response == CoreResponse(
            response_content=1,
            status=CoreStatus.SUCCESSFUL_GET,
            message=f"got id for address: {address}",
        )

    def test_should_fail_address_not_found(self, interactor: WalletsInteractor) -> None:
        address = "1_address_2"
        response = interactor.get_wallet_id(address)
        assert response == CoreResponse(
            response_content=-1,
            status=CoreStatus.INVALID_REQUEST,
            message=f"wallet address: {address} doesn't exist",
        )


class TestGetUserWallets:
    @classmethod
    @pytest.fixture
    @cache
    def interactor(cls) -> WalletsInteractor:
        # required for wallets_repository to be created
        connection = connect(":memory:", check_same_thread=False)
        users_repository = UsersSqlRepository(connection)
        users_repository.create_user("test_1", "test_1_key")
        users_repository.create_user("test_2", "test_2_key")

        wallets_repository = WalletsSqlRepository(connection)
        wallets_repository.create_wallet(1, "1_address_1", 100000000)
        wallets_repository.create_wallet(1, "1_address_2", 100000000)
        wallets_repository.create_wallet(1, "1_address_3", 100000000)
        return WalletsInteractor(
            wallet_repository=wallets_repository,
            converter=MockConverter(),
        )

    def test_should_succeed(self, interactor: WalletsInteractor) -> None:
        user_id = 1
        response = interactor.get_user_wallets(user_id)
        assert response == CoreResponse(
            response_content=[1, 2, 3],
            status=CoreStatus.SUCCESSFUL_GET,
            message=f"got wallets for user: {user_id}",
        )

    def test_should_succeed_empty_list(self, interactor: WalletsInteractor) -> None:
        user_id = 2
        response = interactor.get_user_wallets(user_id)
        assert response == CoreResponse(
            response_content=[],
            status=CoreStatus.SUCCESSFUL_GET,
            message=f"got wallets for user: {user_id}",
        )


class TestCheckWalletValidity:
    @classmethod
    @pytest.fixture
    @cache
    def interactor(cls) -> WalletsInteractor:
        # required for wallets_repository to be created
        connection = connect(":memory:", check_same_thread=False)
        users_repository = UsersSqlRepository(connection)
        users_repository.create_user("test_1", "test_1_key")

        wallets_repository = WalletsSqlRepository(connection)
        wallets_repository.create_wallet(1, "1_address_1", 100000000)
        return WalletsInteractor(
            wallet_repository=wallets_repository,
            converter=MockConverter(),
        )

    def test_should_succeed(self, interactor: WalletsInteractor) -> None:
        address = "1_address_1"
        response = interactor.check_wallet_exists(address)
        assert response == CoreResponse(
            response_content=True,
            status=CoreStatus.SUCCESSFUL_GET,
            message=f"wallet address: {address} valid",
        )

    def test_should_fail_invalid_request(self, interactor: WalletsInteractor) -> None:
        address = "1_address_2"
        response = interactor.check_wallet_exists(address)
        assert response == CoreResponse(
            response_content=-1,
            status=CoreStatus.INVALID_REQUEST,
            message=f"wallet address: {address} invalid",
        )


class TestGetWalletBalance:
    @classmethod
    @pytest.fixture
    @cache
    def interactor(cls) -> WalletsInteractor:
        # required for wallets_repository to be created
        connection = connect(":memory:", check_same_thread=False)
        users_repository = UsersSqlRepository(connection)
        users_repository.create_user("test_1", "test_1_key")

        wallets_repository = WalletsSqlRepository(connection)
        wallets_repository.create_wallet(1, "1_address_1", 100000000)
        return WalletsInteractor(
            wallet_repository=wallets_repository,
            converter=MockConverter(),
        )

    def test_should_succeed(self, interactor: WalletsInteractor) -> None:
        address = "1_address_1"
        satoshi_balance = 100000000
        usd_balance = Decimal(2)
        response = interactor.get_wallet_balance(address)
        assert response == CoreResponse(
            response_content=WalletResponse(address, satoshi_balance, usd_balance),
            status=CoreStatus.SUCCESSFUL_GET,
            message=f"successfully retrieved balance for address: {address}",
        )

    def test_should_fail_invalid_request(self, interactor: WalletsInteractor) -> None:
        address = "1_address_2"
        response = interactor.get_wallet_balance(address)
        assert response == CoreResponse(
            response_content=BadWalletResponse,
            status=CoreStatus.INVALID_REQUEST,
            message=f"wallet address: {address} invalid",
        )


class TestCheckOwnership:
    @classmethod
    @pytest.fixture
    @cache
    def interactor(cls) -> WalletsInteractor:
        # required for wallets_repository to be created
        connection = connect(":memory:", check_same_thread=False)
        users_repository = UsersSqlRepository(connection)
        users_repository.create_user("test_1", "test_1_key")

        wallets_repository = WalletsSqlRepository(connection)
        wallets_repository.create_wallet(1, "1_address_1", 100000000)
        return WalletsInteractor(
            wallet_repository=wallets_repository,
            converter=MockConverter(),
        )

    def test_should_succeed(self, interactor: WalletsInteractor) -> None:
        user_id = 1
        wallet_id = 1
        response = interactor.check_wallet_belongs_to_user(wallet_id, user_id)
        assert response == CoreResponse(
            response_content=True,
            status=CoreStatus.SUCCESSFUL_GET,
            message="Wallet belongs to user",
        )

    def test_should_fail(self, interactor: WalletsInteractor) -> None:
        user_id = 2
        wallet_id = 1
        response = interactor.check_wallet_belongs_to_user(wallet_id, user_id)
        assert response == CoreResponse(
            response_content=False,
            status=CoreStatus.WALLET_DOESNT_BELONG_TO_USER,
            message="Wallet does not belong to user",
        )
