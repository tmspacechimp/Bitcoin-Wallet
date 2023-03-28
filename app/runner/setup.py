import sqlite3
from sqlite3 import Connection

from fastapi import FastAPI

from app.core.facade import BitcoinWalletCore
from app.infra.fastAPI.endpoints.statistics import statistics_api
from app.infra.fastAPI.endpoints.transactions import transactions_api
from app.infra.fastAPI.endpoints.users import users_api
from app.infra.fastAPI.endpoints.wallets import wallets_api
from app.infra.sqlite.transactions import TransactionSqlRepository
from app.infra.sqlite.users import UsersSqlRepository
from app.infra.sqlite.wallets import WalletsSqlRepository


def setup() -> FastAPI:
    app = FastAPI()
    app.include_router(statistics_api)
    app.include_router(transactions_api)
    app.include_router(users_api)
    app.include_router(wallets_api)
    connection: Connection = sqlite3.connect("database.db", check_same_thread=False)
    users_repository = UsersSqlRepository(connection=connection)
    wallets_repository = WalletsSqlRepository(connection=connection)
    transactions_repository = TransactionSqlRepository(connection=connection)
    app.state.core = BitcoinWalletCore.create(
        transactions_repository=transactions_repository,
        users_repository=users_repository,
        wallets_repository=wallets_repository,
    )
    return app
