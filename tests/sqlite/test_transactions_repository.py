import sqlite3
from sqlite3 import Connection

import pytest

from app.infra.sqlite.transactions import TransactionSqlRepository
from app.infra.sqlite.users import UsersSqlRepository
from app.infra.sqlite.wallets import WalletsSqlRepository


@pytest.fixture
def connection() -> Connection:
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    users_sql_repository = UsersSqlRepository(connection)
    users_sql_repository.create_user("test", "test_key")
    users_sql_repository.create_user("test1", "test_key1")
    wallets_sql_repository = WalletsSqlRepository(connection)
    user_id = users_sql_repository.get_user_id("test_key")
    wallets_sql_repository.create_wallet(user_id, "random", 0)
    user_id = users_sql_repository.get_user_id("test_key1")
    wallets_sql_repository.create_wallet(user_id, "random1", 0)
    return connection


def test_create_transaction(connection: Connection) -> None:
    transactions_sql_repository = TransactionSqlRepository(connection)
    assert transactions_sql_repository.create_transaction(1, 2, 0, 0)


def test_get_statistics(connection: Connection) -> None:
    transactions_sql_repository = TransactionSqlRepository(connection)
    assert transactions_sql_repository.create_transaction(1, 2, 1000, 15)
    assert transactions_sql_repository.get_statistics() == (1, 15)
