from functools import cache
from sqlite3 import connect
from typing import List, Tuple

import pytest

from app.core.interactors.transactions import TransactionsInteractor
from app.core.models.resp.core_response import CoreStatus
from app.core.models.resp.statistics import StatisticsResponse
from app.core.models.resp.transaction import (
    GetTransactionsResponse,
    TransactionResponse,
)
from app.infra.sqlite.transactions import TransactionSqlRepository
from app.infra.sqlite.users import UsersSqlRepository
from app.infra.sqlite.wallets import WalletsSqlRepository


class TestCreateTransaction:
    @classmethod
    @pytest.fixture
    @cache
    def params(cls) -> Tuple[TransactionsInteractor, List[int]]:
        # required for transaction_repository to be created
        connection = connect(":memory:", check_same_thread=False)
        users_repository = UsersSqlRepository(connection)
        users_repository.create_user("test", "test_1_key")
        users_repository.create_user("test_2", "test_2_key")

        wallets_repository = WalletsSqlRepository(connection)
        wallets_repository.create_wallet(1, "1_address_1", 100000000)
        wallets_repository.create_wallet(1, "1_address_2", 100000000)
        wallets_repository.create_wallet(1, "1_address_3", 100000000)
        wallets_repository.create_wallet(2, "2_address_1", 100000000)
        wallets_repository.create_wallet(2, "2_address_2", 100000000)
        wallets_repository.create_wallet(2, "2_address_3", 100000000)
        wallet_ids = [
            wallets_repository.get_wallet_id("1_address_1"),
            wallets_repository.get_wallet_id("1_address_2"),
            wallets_repository.get_wallet_id("1_address_3"),
            wallets_repository.get_wallet_id("2_address_1"),
            wallets_repository.get_wallet_id("2_address_2"),
            wallets_repository.get_wallet_id("2_address_3"),
        ]
        transaction_repository = TransactionSqlRepository(connection)
        return TransactionsInteractor(transaction_repository), wallet_ids

    def test_should_succeed(
        self, params: Tuple[TransactionsInteractor, List[int]]
    ) -> None:
        interactor = params[0]
        wallet_ids = params[1]
        from_id = wallet_ids[0]
        to_id = wallet_ids[3]
        response = interactor.create(from_id, to_id, 1000, 15)
        assert response.status == CoreStatus.SUCCESSFUL_POST


class TestGetWalletTransactions:
    @classmethod
    @pytest.fixture
    @cache
    def params(cls) -> Tuple[TransactionsInteractor, List[int]]:
        # required for transaction_repository to be created
        connection = connect(":memory:", check_same_thread=False)
        users_repository = UsersSqlRepository(connection)
        users_repository.create_user("test", "test_1_key")
        users_repository.create_user("test_2", "test_2_key")

        wallets_repository = WalletsSqlRepository(connection)
        wallets_repository.create_wallet(1, "1_address_1", 100000000)
        wallets_repository.create_wallet(1, "1_address_2", 100000000)
        wallets_repository.create_wallet(1, "1_address_3", 100000000)
        wallets_repository.create_wallet(2, "2_address_1", 100000000)
        wallets_repository.create_wallet(2, "2_address_2", 100000000)
        wallets_repository.create_wallet(2, "2_address_3", 100000000)
        wallet_ids = [
            wallets_repository.get_wallet_id("1_address_1"),
            wallets_repository.get_wallet_id("1_address_2"),
            wallets_repository.get_wallet_id("1_address_3"),
            wallets_repository.get_wallet_id("2_address_1"),
            wallets_repository.get_wallet_id("2_address_2"),
            wallets_repository.get_wallet_id("2_address_3"),
        ]
        transaction_repository = TransactionSqlRepository(connection)
        return TransactionsInteractor(transaction_repository), wallet_ids

    def test_should_succeed(
        self, params: Tuple[TransactionsInteractor, List[int]]
    ) -> None:
        interactor = params[0]
        wallet_ids = params[1]
        from_id = wallet_ids[0]
        interactor.create(from_id, wallet_ids[3], 1000, 15)
        interactor.create(from_id, wallet_ids[4], 10000, 15)
        interactor.create(from_id, wallet_ids[5], 3000, 15)
        interactor.create(wallet_ids[5], from_id, 1000, 15)
        response = interactor.get([from_id])
        assert response.response_content == GetTransactionsResponse(
            [
                TransactionResponse("1_address_1", "2_address_1", 1000),
                TransactionResponse("1_address_1", "2_address_2", 10000),
                TransactionResponse("1_address_1", "2_address_3", 3000),
                TransactionResponse("2_address_3", "1_address_1", 1000),
            ]
        )
        assert response.status == CoreStatus.SUCCESSFUL_GET

    def test_should_succeed_empty(
        self, params: Tuple[TransactionsInteractor, List[int]]
    ) -> None:
        interactor = params[0]
        wallet_ids = params[1]
        from_id = wallet_ids[0]
        interactor.create(from_id, wallet_ids[3], 1000, 15)
        interactor.create(from_id, wallet_ids[4], 10000, 15)
        interactor.create(from_id, wallet_ids[5], 3000, 15)
        interactor.create(wallet_ids[5], from_id, 1000, 15)
        response = interactor.get([wallet_ids[1], wallet_ids[2]])
        assert response.response_content == GetTransactionsResponse([])
        assert response.status == CoreStatus.SUCCESSFUL_GET

    def test_should_succeed_empty_arguments(
        self, params: Tuple[TransactionsInteractor, List[int]]
    ) -> None:
        interactor = params[0]
        wallet_ids = params[1]
        from_id = wallet_ids[0]
        interactor.create(from_id, wallet_ids[3], 1000, 15)
        interactor.create(from_id, wallet_ids[4], 10000, 15)
        interactor.create(from_id, wallet_ids[5], 3000, 15)
        interactor.create(wallet_ids[5], from_id, 1000, 15)
        response = interactor.get([])
        assert response.response_content == GetTransactionsResponse([])
        assert response.status == CoreStatus.SUCCESSFUL_GET


class TestGetTransactionsStatistics:
    @classmethod
    @pytest.fixture
    @cache
    def params(cls) -> Tuple[TransactionsInteractor, List[int]]:
        # required for transaction_repository to be created
        connection = connect(":memory:", check_same_thread=False)
        users_repository = UsersSqlRepository(connection)
        users_repository.create_user("test", "test_1_key")
        users_repository.create_user("test_2", "test_2_key")

        wallets_repository = WalletsSqlRepository(connection)
        wallets_repository.create_wallet(1, "1_address_1", 100000000)
        wallets_repository.create_wallet(1, "1_address_2", 100000000)
        wallets_repository.create_wallet(1, "1_address_3", 100000000)
        wallets_repository.create_wallet(2, "2_address_1", 100000000)
        wallets_repository.create_wallet(2, "2_address_2", 100000000)
        wallets_repository.create_wallet(2, "2_address_3", 100000000)
        wallet_ids = [
            wallets_repository.get_wallet_id("1_address_1"),
            wallets_repository.get_wallet_id("1_address_2"),
            wallets_repository.get_wallet_id("1_address_3"),
            wallets_repository.get_wallet_id("2_address_1"),
            wallets_repository.get_wallet_id("2_address_2"),
            wallets_repository.get_wallet_id("2_address_3"),
        ]
        transaction_repository = TransactionSqlRepository(connection)
        return TransactionsInteractor(transaction_repository), wallet_ids

    def test_empty_statistics(
        self, params: Tuple[TransactionsInteractor, List[int]]
    ) -> None:
        interactor = params[0]
        response = interactor.get_statistics()
        assert response.response_content == StatisticsResponse(0, 0)
        assert response.status == CoreStatus.SUCCESSFUL_GET

    def test_get_statistics(
        self, params: Tuple[TransactionsInteractor, List[int]]
    ) -> None:
        interactor = params[0]
        wallet_ids = params[1]
        interactor.create(wallet_ids[0], wallet_ids[3], 1000000, 2000)
        interactor.create(wallet_ids[1], wallet_ids[4], 10000, 1500)
        interactor.create(wallet_ids[1], wallet_ids[5], 4000, 1000)
        interactor.create(wallet_ids[0], wallet_ids[5], 200000, 350)
        interactor.create(wallet_ids[4], wallet_ids[0], 3000000, 200)
        interactor.create(wallet_ids[5], wallet_ids[2], 7000, 100)

        response = interactor.get_statistics()
        assert response.response_content == StatisticsResponse(6, 5150)
        assert response.status == CoreStatus.SUCCESSFUL_GET
