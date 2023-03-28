from functools import cache
from math import ceil
from sqlite3 import connect
from typing import List, Tuple

import pytest

from app.core.constants.constants import ADMIN_KEY, COMMISSION_PERCENT, INITIAL_BALANCE
from app.core.facade import BitcoinWalletCore
from app.core.models.req.transaction import TransactionRequest
from app.core.models.req.user import CreateUserRequest
from app.core.models.resp.core_response import CoreStatus
from app.core.models.resp.transaction import (
    GetTransactionsResponse,
    TransactionResponse,
)
from app.infra.sqlite.transactions import TransactionSqlRepository
from app.infra.sqlite.users import UsersSqlRepository
from app.infra.sqlite.wallets import WalletsSqlRepository


class TestCreateUser:
    @classmethod
    @pytest.fixture
    @cache
    def core(cls) -> BitcoinWalletCore:
        connection = connect(":memory:", check_same_thread=False)
        users_repository = UsersSqlRepository(connection=connection)
        wallets_repository = WalletsSqlRepository(connection=connection)
        transactions_repository = TransactionSqlRepository(connection=connection)
        return BitcoinWalletCore.create(
            transactions_repository=transactions_repository,
            users_repository=users_repository,
            wallets_repository=wallets_repository,
        )

    def test_should_create(self, core: BitcoinWalletCore) -> None:
        request = CreateUserRequest(email="test")
        response = core.create_user(request)
        assert response.status == CoreStatus.USER_CREATED

    def test_email_already_in_use(self, core: BitcoinWalletCore) -> None:
        request = CreateUserRequest(email="test")
        core.create_user(request)
        response = core.create_user(request)
        assert response.status == CoreStatus.EMAIL_ALREADY_IN_USE


class TestCreateWallet:
    @classmethod
    @pytest.fixture
    @cache
    def core(cls) -> BitcoinWalletCore:
        connection = connect(":memory:", check_same_thread=False)
        users_repository = UsersSqlRepository(connection=connection)
        wallets_repository = WalletsSqlRepository(connection=connection)
        transactions_repository = TransactionSqlRepository(connection=connection)
        return BitcoinWalletCore.create(
            transactions_repository=transactions_repository,
            users_repository=users_repository,
            wallets_repository=wallets_repository,
        )

    def test_should_create(self, core: BitcoinWalletCore) -> None:
        request = CreateUserRequest(email="test")
        user_response = core.create_user(request)
        api_key = user_response.response_content.api_key
        wallet_response = core.create_wallet(api_key)
        assert wallet_response.status == CoreStatus.SUCCESSFUL_POST

    def test_wallet_limit_exceeded(self, core: BitcoinWalletCore) -> None:
        request = CreateUserRequest(email="test")
        user_response = core.create_user(request)
        api_key = user_response.response_content.api_key
        core.create_wallet(api_key)
        core.create_wallet(api_key)
        wallet_response = core.create_wallet(api_key)
        assert wallet_response.status == CoreStatus.SUCCESSFUL_POST
        new_response = core.create_wallet(api_key)
        assert new_response.status == CoreStatus.WALLET_LIMIT_REACHED

    def test_user_not_found(self, core: BitcoinWalletCore) -> None:
        api_key = "not found"
        response = core.create_wallet(api_key)
        assert response.status == CoreStatus.INVALID_API_KEY

    def test_no_api_key(self, core: BitcoinWalletCore) -> None:
        response = core.create_wallet(None)
        assert response.status == CoreStatus.INVALID_API_KEY


class TestCreateTransaction:
    @classmethod
    @pytest.fixture
    @cache
    def params(cls) -> Tuple[BitcoinWalletCore, List[str], List[str]]:
        connection = connect(":memory:", check_same_thread=False)
        users_repository = UsersSqlRepository(connection=connection)
        wallets_repository = WalletsSqlRepository(connection=connection)
        transactions_repository = TransactionSqlRepository(connection=connection)
        core = BitcoinWalletCore.create(
            transactions_repository=transactions_repository,
            users_repository=users_repository,
            wallets_repository=wallets_repository,
        )
        first_request = CreateUserRequest(email="test")
        first_user_response = core.create_user(first_request)
        second_request = CreateUserRequest(email="test1")
        second_user_response = core.create_user(second_request)
        first_api_key = first_user_response.response_content.api_key
        second_api_key = second_user_response.response_content.api_key
        first_wallet_response = core.create_wallet(first_api_key)
        second_wallet_response = core.create_wallet(second_api_key)
        return (
            core,
            [first_api_key, second_api_key],
            [
                first_wallet_response.response_content.address,
                second_wallet_response.response_content.address,
            ],
        )

    def test_should_create(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        wallet_addresses = params[2]
        transaction_response = core.make_transaction(
            api_keys[0],
            TransactionRequest(
                from_address=wallet_addresses[0],
                to_address=wallet_addresses[1],
                amount_in_satoshi=100,
            ),
        )
        assert transaction_response.status == CoreStatus.SUCCESSFUL_POST

    def test_user_not_found(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        wallet_addresses = params[2]
        transaction_response = core.make_transaction(
            "not found",
            TransactionRequest(
                from_address=wallet_addresses[0],
                to_address=wallet_addresses[1],
                amount_in_satoshi=100,
            ),
        )
        assert transaction_response.status == CoreStatus.INVALID_API_KEY

    def test_no_api_key(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        wallet_addresses = params[2]
        transaction_response = core.make_transaction(
            None,
            TransactionRequest(
                from_address=wallet_addresses[0],
                to_address=wallet_addresses[1],
                amount_in_satoshi=100,
            ),
        )
        assert transaction_response.status == CoreStatus.INVALID_API_KEY

    def test_illegal_address(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        wallet_addresses = params[2]
        transaction_response = core.make_transaction(
            api_keys[0],
            TransactionRequest(
                from_address="not found",
                to_address=wallet_addresses[1],
                amount_in_satoshi=100,
            ),
        )
        assert transaction_response.status == CoreStatus.WALLET_DOESNT_BELONG_TO_USER

    def test_does_not_belong(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        wallet_addresses = params[2]
        transaction_response = core.make_transaction(
            api_keys[1],
            TransactionRequest(
                from_address=wallet_addresses[0],
                to_address=wallet_addresses[1],
                amount_in_satoshi=100,
            ),
        )
        assert transaction_response.status == CoreStatus.WALLET_DOESNT_BELONG_TO_USER

    def test_illegal_receiver_wallet(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        wallet_addresses = params[2]
        transaction_response = core.make_transaction(
            api_keys[0],
            TransactionRequest(
                from_address=wallet_addresses[0],
                to_address="not found",
                amount_in_satoshi=100,
            ),
        )
        assert transaction_response.status == CoreStatus.INVALID_REQUEST

    def test_insufficient_balance(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        wallet_addresses = params[2]
        transaction_response = core.make_transaction(
            api_keys[0],
            TransactionRequest(
                from_address=wallet_addresses[0],
                to_address=wallet_addresses[1],
                amount_in_satoshi=10000000000000,
            ),
        )
        assert transaction_response.status == CoreStatus.INSUFFICIENT_FUNDS


class TestGetWalletBalance:
    @classmethod
    @pytest.fixture
    @cache
    def params(cls) -> Tuple[BitcoinWalletCore, List[str], List[str]]:
        connection = connect(":memory:", check_same_thread=False)
        users_repository = UsersSqlRepository(connection=connection)
        wallets_repository = WalletsSqlRepository(connection=connection)
        transactions_repository = TransactionSqlRepository(connection=connection)
        core = BitcoinWalletCore.create(
            transactions_repository=transactions_repository,
            users_repository=users_repository,
            wallets_repository=wallets_repository,
        )
        first_request = CreateUserRequest(email="test")
        first_user_response = core.create_user(first_request)
        second_request = CreateUserRequest(email="test1")
        second_user_response = core.create_user(second_request)
        first_api_key = first_user_response.response_content.api_key
        second_api_key = second_user_response.response_content.api_key
        first_wallet_response = core.create_wallet(first_api_key)
        second_wallet_response = core.create_wallet(second_api_key)
        return (
            core,
            [first_api_key, second_api_key],
            [
                first_wallet_response.response_content.address,
                second_wallet_response.response_content.address,
            ],
        )

    def test_initial_balance(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        wallet_addresses = params[2]
        wallet_response = core.get_wallet_balance(api_keys[0], wallet_addresses[0])
        assert wallet_response.status == CoreStatus.SUCCESSFUL_GET
        assert wallet_response.response_content.address == wallet_addresses[0]
        assert wallet_response.response_content.satoshi_balance == INITIAL_BALANCE

    def test_user_not_found(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        wallet_addresses = params[2]
        wallet_response = core.get_wallet_balance("not found", wallet_addresses[0])
        assert wallet_response.status == CoreStatus.INVALID_API_KEY

    def test_no_api_key(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        wallet_addresses = params[2]
        wallet_response = core.get_wallet_balance(None, wallet_addresses[0])
        assert wallet_response.status == CoreStatus.INVALID_API_KEY

    def test_does_not_belong(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        wallet_addresses = params[2]
        wallet_response = core.get_wallet_balance(api_keys[1], wallet_addresses[0])
        assert wallet_response.status == CoreStatus.WALLET_DOESNT_BELONG_TO_USER

    def test_illegal_address(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        wallet_response = core.get_wallet_balance(api_keys[1], "not found")
        assert wallet_response.status == CoreStatus.WALLET_DOESNT_BELONG_TO_USER

    def test_balance_after_successful_transaction(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        wallet_addresses = params[2]
        pre_first_wallet_response = core.get_wallet_balance(
            api_keys[0], wallet_addresses[0]
        )
        assert pre_first_wallet_response.status == CoreStatus.SUCCESSFUL_GET
        assert pre_first_wallet_response.response_content.address == wallet_addresses[0]
        assert (
            pre_first_wallet_response.response_content.satoshi_balance
            == INITIAL_BALANCE
        )
        pre_second_wallet_response = core.get_wallet_balance(
            api_keys[1], wallet_addresses[1]
        )
        assert pre_second_wallet_response.status == CoreStatus.SUCCESSFUL_GET
        assert (
            pre_second_wallet_response.response_content.address == wallet_addresses[1]
        )
        assert (
            pre_second_wallet_response.response_content.satoshi_balance
            == INITIAL_BALANCE
        )
        core.make_transaction(
            api_keys[0],
            TransactionRequest(
                from_address=wallet_addresses[0],
                to_address=wallet_addresses[1],
                amount_in_satoshi=1000,
            ),
        )
        first_wallet_response = core.get_wallet_balance(
            api_keys[0], wallet_addresses[0]
        )
        assert first_wallet_response.status == CoreStatus.SUCCESSFUL_GET
        assert first_wallet_response.response_content.address == wallet_addresses[0]
        assert (
            first_wallet_response.response_content.satoshi_balance
            == INITIAL_BALANCE - 1000 - int(ceil(1000 * COMMISSION_PERCENT / 100))
        )
        second_wallet_response = core.get_wallet_balance(
            api_keys[1], wallet_addresses[1]
        )
        assert second_wallet_response.status == CoreStatus.SUCCESSFUL_GET
        assert second_wallet_response.response_content.address == wallet_addresses[1]
        assert (
            second_wallet_response.response_content.satoshi_balance
            == INITIAL_BALANCE + 1000
        )

    def test_balance_after_failed_transaction(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        wallet_addresses = params[2]
        pre_first_wallet_response = core.get_wallet_balance(
            api_keys[0], wallet_addresses[0]
        )
        assert pre_first_wallet_response.status == CoreStatus.SUCCESSFUL_GET
        assert pre_first_wallet_response.response_content.address == wallet_addresses[0]
        assert (
            pre_first_wallet_response.response_content.satoshi_balance
            == INITIAL_BALANCE
        )
        pre_second_wallet_response = core.get_wallet_balance(
            api_keys[1], wallet_addresses[1]
        )
        assert pre_second_wallet_response.status == CoreStatus.SUCCESSFUL_GET
        assert (
            pre_second_wallet_response.response_content.address == wallet_addresses[1]
        )
        assert (
            pre_second_wallet_response.response_content.satoshi_balance
            == INITIAL_BALANCE
        )
        transaction_response = core.make_transaction(
            api_keys[0],
            TransactionRequest(
                from_address=wallet_addresses[0],
                to_address=wallet_addresses[1],
                amount_in_satoshi=10000000000,
            ),
        )
        assert transaction_response.status == CoreStatus.INSUFFICIENT_FUNDS
        first_wallet_response = core.get_wallet_balance(
            api_keys[0], wallet_addresses[0]
        )
        assert first_wallet_response.status == CoreStatus.SUCCESSFUL_GET
        assert first_wallet_response.response_content.address == wallet_addresses[0]
        assert first_wallet_response.response_content.satoshi_balance == INITIAL_BALANCE
        second_wallet_response = core.get_wallet_balance(
            api_keys[1], wallet_addresses[1]
        )
        assert second_wallet_response.status == CoreStatus.SUCCESSFUL_GET
        assert second_wallet_response.response_content.address == wallet_addresses[1]
        assert (
            second_wallet_response.response_content.satoshi_balance == INITIAL_BALANCE
        )

    def test_same_users_wallets_no_commission(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        second_wallet_address = core.create_wallet(api_keys[0]).response_content.address
        wallet_addresses = params[2]
        pre_first_wallet_response = core.get_wallet_balance(
            api_keys[0], wallet_addresses[0]
        )
        assert pre_first_wallet_response.status == CoreStatus.SUCCESSFUL_GET
        assert pre_first_wallet_response.response_content.address == wallet_addresses[0]
        assert (
            pre_first_wallet_response.response_content.satoshi_balance
            == INITIAL_BALANCE
        )
        pre_second_wallet_response = core.get_wallet_balance(
            api_keys[0], second_wallet_address
        )
        assert pre_second_wallet_response.status == CoreStatus.SUCCESSFUL_GET
        assert (
            pre_second_wallet_response.response_content.address == second_wallet_address
        )
        assert (
            pre_second_wallet_response.response_content.satoshi_balance
            == INITIAL_BALANCE
        )
        core.make_transaction(
            api_keys[0],
            TransactionRequest(
                from_address=wallet_addresses[0],
                to_address=second_wallet_address,
                amount_in_satoshi=1000,
            ),
        )
        first_wallet_response = core.get_wallet_balance(
            api_keys[0], wallet_addresses[0]
        )
        assert first_wallet_response.status == CoreStatus.SUCCESSFUL_GET
        assert first_wallet_response.response_content.address == wallet_addresses[0]
        assert (
            first_wallet_response.response_content.satoshi_balance
            == INITIAL_BALANCE - 1000
        )
        second_wallet_response = core.get_wallet_balance(
            api_keys[0], second_wallet_address
        )
        assert second_wallet_response.status == CoreStatus.SUCCESSFUL_GET
        assert second_wallet_response.response_content.address == second_wallet_address
        assert (
            second_wallet_response.response_content.satoshi_balance
            == INITIAL_BALANCE + 1000
        )


class TestGetTransactions:
    @classmethod
    @pytest.fixture
    @cache
    def params(cls) -> Tuple[BitcoinWalletCore, List[str], List[str]]:
        connection = connect(":memory:", check_same_thread=False)
        users_repository = UsersSqlRepository(connection=connection)
        wallets_repository = WalletsSqlRepository(connection=connection)
        transactions_repository = TransactionSqlRepository(connection=connection)
        core = BitcoinWalletCore.create(
            transactions_repository=transactions_repository,
            users_repository=users_repository,
            wallets_repository=wallets_repository,
        )
        first_request = CreateUserRequest(email="test")
        first_user_response = core.create_user(first_request)
        second_request = CreateUserRequest(email="test1")
        second_user_response = core.create_user(second_request)
        first_api_key = first_user_response.response_content.api_key
        second_api_key = second_user_response.response_content.api_key
        first_wallet_response = core.create_wallet(first_api_key)
        second_wallet_response = core.create_wallet(second_api_key)
        return (
            core,
            [first_api_key, second_api_key],
            [
                first_wallet_response.response_content.address,
                second_wallet_response.response_content.address,
            ],
        )

    def test_should_succeed_empty(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        transactions_response = core.get_transactions(api_keys[0])
        assert transactions_response.response_content == GetTransactionsResponse([])
        assert transactions_response.status == CoreStatus.SUCCESSFUL_GET

    def test_user_not_found(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        transactions_response = core.get_transactions("not found")
        assert transactions_response.status == CoreStatus.INVALID_API_KEY

    def test_no_api_key(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        transactions_response = core.get_transactions(None)
        assert transactions_response.status == CoreStatus.INVALID_API_KEY

    def test_correct_list(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        second_wallet_address = core.create_wallet(api_keys[0]).response_content.address
        third_wallet_address = core.create_wallet(api_keys[0]).response_content.address
        wallet_addresses = params[2]
        core.make_transaction(
            api_keys[0],
            TransactionRequest(
                from_address=wallet_addresses[0],
                to_address=wallet_addresses[1],
                amount_in_satoshi=1000,
            ),
        )
        core.make_transaction(
            api_keys[0],
            TransactionRequest(
                from_address=second_wallet_address,
                to_address=wallet_addresses[1],
                amount_in_satoshi=1000,
            ),
        )
        core.make_transaction(
            api_keys[0],
            TransactionRequest(
                from_address=third_wallet_address,
                to_address=wallet_addresses[1],
                amount_in_satoshi=1000,
            ),
        )
        core.make_transaction(
            api_keys[1],
            TransactionRequest(
                from_address=wallet_addresses[1],
                to_address=wallet_addresses[0],
                amount_in_satoshi=1000,
            ),
        )
        core.make_transaction(
            api_keys[1],
            TransactionRequest(
                from_address=wallet_addresses[1],
                to_address=third_wallet_address,
                amount_in_satoshi=1000,
            ),
        )
        transactions_response = core.get_transactions(api_keys[0])
        assert transactions_response.status == CoreStatus.SUCCESSFUL_GET
        assert transactions_response.response_content == GetTransactionsResponse(
            [
                TransactionResponse(
                    from_address=wallet_addresses[0],
                    to_address=wallet_addresses[1],
                    amount_in_satoshi=1000,
                ),
                TransactionResponse(
                    from_address=second_wallet_address,
                    to_address=wallet_addresses[1],
                    amount_in_satoshi=1000,
                ),
                TransactionResponse(
                    from_address=third_wallet_address,
                    to_address=wallet_addresses[1],
                    amount_in_satoshi=1000,
                ),
                TransactionResponse(
                    from_address=wallet_addresses[1],
                    to_address=wallet_addresses[0],
                    amount_in_satoshi=1000,
                ),
                TransactionResponse(
                    from_address=wallet_addresses[1],
                    to_address=third_wallet_address,
                    amount_in_satoshi=1000,
                ),
            ]
        )

    def test_failed_transactions_included(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        second_wallet_address = core.create_wallet(api_keys[0]).response_content.address
        third_wallet_address = core.create_wallet(api_keys[0]).response_content.address
        wallet_addresses = params[2]
        core.make_transaction(
            api_keys[0],
            TransactionRequest(
                from_address=wallet_addresses[0],
                to_address=wallet_addresses[1],
                amount_in_satoshi=5000,
            ),
        )
        core.make_transaction(
            api_keys[0],
            TransactionRequest(
                from_address=second_wallet_address,
                to_address=wallet_addresses[1],
                amount_in_satoshi=800,
            ),
        )
        core.make_transaction(
            api_keys[1],
            TransactionRequest(
                from_address=wallet_addresses[1],
                to_address=wallet_addresses[0],
                amount_in_satoshi=2500000000000000,
            ),
        )
        core.make_transaction(
            api_keys[0],
            TransactionRequest(
                from_address=third_wallet_address,
                to_address=wallet_addresses[1],
                amount_in_satoshi=12000,
            ),
        )
        core.make_transaction(
            api_keys[1],
            TransactionRequest(
                from_address=wallet_addresses[1],
                to_address=wallet_addresses[0],
                amount_in_satoshi=3000,
            ),
        )
        core.make_transaction(
            api_keys[1],
            TransactionRequest(
                from_address=wallet_addresses[1],
                to_address=second_wallet_address,
                amount_in_satoshi=3000000000000000,
            ),
        )
        core.make_transaction(
            api_keys[1],
            TransactionRequest(
                from_address=wallet_addresses[1],
                to_address=third_wallet_address,
                amount_in_satoshi=75000,
            ),
        )
        transactions_response = core.get_transactions(api_keys[0])
        assert transactions_response.status == CoreStatus.SUCCESSFUL_GET
        assert transactions_response.response_content == GetTransactionsResponse(
            [
                TransactionResponse(
                    from_address=wallet_addresses[0],
                    to_address=wallet_addresses[1],
                    amount_in_satoshi=5000,
                ),
                TransactionResponse(
                    from_address=second_wallet_address,
                    to_address=wallet_addresses[1],
                    amount_in_satoshi=800,
                ),
                TransactionResponse(
                    from_address=third_wallet_address,
                    to_address=wallet_addresses[1],
                    amount_in_satoshi=12000,
                ),
                TransactionResponse(
                    from_address=wallet_addresses[1],
                    to_address=wallet_addresses[0],
                    amount_in_satoshi=3000,
                ),
                TransactionResponse(
                    from_address=wallet_addresses[1],
                    to_address=third_wallet_address,
                    amount_in_satoshi=75000,
                ),
            ]
        )


class TestGetWalletTransactions:
    @classmethod
    @pytest.fixture
    @cache
    def params(cls) -> Tuple[BitcoinWalletCore, List[str], List[str]]:
        connection = connect(":memory:", check_same_thread=False)
        users_repository = UsersSqlRepository(connection=connection)
        wallets_repository = WalletsSqlRepository(connection=connection)
        transactions_repository = TransactionSqlRepository(connection=connection)
        core = BitcoinWalletCore.create(
            transactions_repository=transactions_repository,
            users_repository=users_repository,
            wallets_repository=wallets_repository,
        )
        first_request = CreateUserRequest(email="test")
        first_user_response = core.create_user(first_request)
        second_request = CreateUserRequest(email="test1")
        second_user_response = core.create_user(second_request)
        first_api_key = first_user_response.response_content.api_key
        second_api_key = second_user_response.response_content.api_key
        first_wallet_response = core.create_wallet(first_api_key)
        second_wallet_response = core.create_wallet(second_api_key)
        second_user_second_wallet = core.create_wallet(
            second_api_key
        ).response_content.address
        second_user_third_wallet = core.create_wallet(
            second_api_key
        ).response_content.address
        core.make_transaction(
            first_api_key,
            TransactionRequest(
                from_address=first_wallet_response.response_content.address,
                to_address=second_wallet_response.response_content.address,
                amount_in_satoshi=100000,
            ),
        )
        core.make_transaction(
            first_api_key,
            TransactionRequest(
                from_address=first_wallet_response.response_content.address,
                to_address=second_user_third_wallet,
                amount_in_satoshi=70000,
            ),
        )
        core.make_transaction(
            second_api_key,
            TransactionRequest(
                from_address=second_user_second_wallet,
                to_address=first_wallet_response.response_content.address,
                amount_in_satoshi=12000,
            ),
        )
        core.make_transaction(
            first_api_key,
            TransactionRequest(
                from_address=first_wallet_response.response_content.address,
                to_address=second_user_second_wallet,
                amount_in_satoshi=5000,
            ),
        )
        return (
            core,
            [first_api_key, second_api_key],
            [
                first_wallet_response.response_content.address,
                second_wallet_response.response_content.address,
                second_user_second_wallet,
                second_user_third_wallet,
            ],
        )

    def test_should_succeed_empty(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        other_wallet = core.create_wallet(api_keys[0])
        transactions_response = core.get_transactions_for_wallet(
            api_keys[0], other_wallet.response_content.address
        )
        assert transactions_response.status == CoreStatus.SUCCESSFUL_GET
        assert transactions_response.response_content == GetTransactionsResponse([])

    def test_user_not_found(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        wallet_addresses = params[2]
        transactions_response = core.get_transactions_for_wallet(
            "not found", wallet_addresses[1]
        )
        assert transactions_response.status == CoreStatus.INVALID_API_KEY

    def test_no_api_key(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        wallet_addresses = params[2]
        transactions_response = core.get_transactions_for_wallet(
            None, wallet_addresses[1]
        )
        assert transactions_response.status == CoreStatus.INVALID_API_KEY

    def test_does_not_belong(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        wallet_addresses = params[2]
        transactions_response = core.get_transactions_for_wallet(
            api_keys[0], wallet_addresses[1]
        )
        assert transactions_response.status == CoreStatus.WALLET_DOESNT_BELONG_TO_USER

    def test_illegal_address(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        transactions_response = core.get_transactions_for_wallet(
            api_keys[0], "not found"
        )
        assert transactions_response.status == CoreStatus.INVALID_REQUEST

    def test_should_succeed_correct_list(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        wallet_addresses = params[2]
        transaction_response = core.get_transactions_for_wallet(
            api_keys[0], wallet_addresses[0]
        )
        assert transaction_response.status == CoreStatus.SUCCESSFUL_GET
        assert transaction_response.response_content == GetTransactionsResponse(
            [
                TransactionResponse(wallet_addresses[0], wallet_addresses[1], 100000),
                TransactionResponse(wallet_addresses[0], wallet_addresses[3], 70000),
                TransactionResponse(wallet_addresses[2], wallet_addresses[0], 12000),
                TransactionResponse(wallet_addresses[0], wallet_addresses[2], 5000),
            ]
        )


class TestGetStatistics:
    @classmethod
    @pytest.fixture
    @cache
    def params(cls) -> Tuple[BitcoinWalletCore, List[str], List[str]]:
        connection = connect(":memory:", check_same_thread=False)
        users_repository = UsersSqlRepository(connection=connection)
        wallets_repository = WalletsSqlRepository(connection=connection)
        transactions_repository = TransactionSqlRepository(connection=connection)
        core = BitcoinWalletCore.create(
            transactions_repository=transactions_repository,
            users_repository=users_repository,
            wallets_repository=wallets_repository,
        )
        first_request = CreateUserRequest(email="test")
        first_user_response = core.create_user(first_request)
        second_request = CreateUserRequest(email="test1")
        second_user_response = core.create_user(second_request)
        first_api_key = first_user_response.response_content.api_key
        second_api_key = second_user_response.response_content.api_key
        first_wallet_response = core.create_wallet(first_api_key)
        second_wallet_response = core.create_wallet(second_api_key)
        return (
            core,
            [first_api_key, second_api_key],
            [
                first_wallet_response.response_content.address,
                second_wallet_response.response_content.address,
            ],
        )

    def test_should_succeed_empty(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        statistics_response = core.get_statistics(ADMIN_KEY)
        assert statistics_response.status == CoreStatus.SUCCESSFUL_GET
        assert statistics_response.response_content.profit_in_satoshi == 0
        assert statistics_response.response_content.num_transaction == 0

    def test_should_fail_wrong_key(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        statistics_response = core.get_statistics("no key")
        assert statistics_response.status == CoreStatus.INVALID_ADMIN_KEY

    def test_should_succeed_correct_list(
        self, params: Tuple[BitcoinWalletCore, List[str], List[str]]
    ) -> None:
        core = params[0]
        api_keys = params[1]
        wallet_addresses = params[2]
        core.make_transaction(
            api_keys[0],
            TransactionRequest(
                from_address=wallet_addresses[0],
                to_address=wallet_addresses[1],
                amount_in_satoshi=10000,
            ),
        )
        core.make_transaction(
            api_keys[1],
            TransactionRequest(
                from_address=wallet_addresses[1],
                to_address=wallet_addresses[0],
                amount_in_satoshi=20000,
            ),
        )
        core.make_transaction(
            api_keys[0],
            TransactionRequest(
                from_address=wallet_addresses[0],
                to_address=wallet_addresses[1],
                amount_in_satoshi=35000,
            ),
        )
        core.make_transaction(
            api_keys[1],
            TransactionRequest(
                from_address=wallet_addresses[0],
                to_address=wallet_addresses[1],
                amount_in_satoshi=12500,
            ),
        )  # won't go through
        core.make_transaction(
            api_keys[1],
            TransactionRequest(
                from_address=wallet_addresses[1],
                to_address=wallet_addresses[0],
                amount_in_satoshi=125000,
            ),
        )
        core.make_transaction(
            api_keys[1],
            TransactionRequest(
                from_address=wallet_addresses[1],
                to_address=wallet_addresses[0],
                amount_in_satoshi=70000,
            ),
        )
        wallet_address = core.create_wallet(
            api_keys[0]
        ).response_content.address  # Non-profitable
        core.make_transaction(
            api_keys[0],
            TransactionRequest(
                from_address=wallet_addresses[0],
                to_address=wallet_address,
                amount_in_satoshi=50000,
            ),
        )
        core.make_transaction(
            api_keys[0],
            TransactionRequest(
                from_address=wallet_address,
                to_address=wallet_addresses[0],
                amount_in_satoshi=38000,
            ),
        )

        statistics_response = core.get_statistics(ADMIN_KEY)
        assert statistics_response.status == CoreStatus.SUCCESSFUL_GET
        assert statistics_response.response_content.num_transaction == 7
        assert statistics_response.response_content.profit_in_satoshi == int(
            ceil(260000 * COMMISSION_PERCENT / 100)
        )
