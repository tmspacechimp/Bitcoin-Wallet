import sqlite3
from sqlite3 import Connection

import pytest

from app.infra.sqlite.users import UsersSqlRepository
from app.infra.sqlite.wallets import WalletsSqlRepository


@pytest.fixture
def connection() -> Connection:
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    users_sql_repository = UsersSqlRepository(connection)
    users_sql_repository.create_user("test", "test_key")
    return connection


def test_create_wallet(connection: Connection) -> None:
    wallet_sql_repository = WalletsSqlRepository(connection)
    assert wallet_sql_repository.create_wallet(1, "random_addr", 0)


def test_get_id(connection: Connection) -> None:
    wallet_sql_repository = WalletsSqlRepository(connection)
    wallet_sql_repository.create_wallet(1, "random_addr", 0)
    assert wallet_sql_repository.get_wallet_id("random_addr") != -1
    assert wallet_sql_repository.get_wallet_id("random_addr") == 1


def test_get_balance(connection: Connection) -> None:
    wallet_sql_repository = WalletsSqlRepository(connection)
    wallet_sql_repository.create_wallet(1, "random_addr", 1)
    assert wallet_sql_repository.get_wallet_balance(address="random_addr") == 1
