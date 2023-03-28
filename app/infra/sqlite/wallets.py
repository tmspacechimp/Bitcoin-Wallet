from sqlite3 import Connection, Cursor, IntegrityError
from typing import List


class WalletsSqlRepository:
    connection: Connection
    _cursor: Cursor

    def __init__(self, connection: Connection) -> None:
        self.connection = connection
        self._cursor = connection.cursor()
        self._cursor.execute(
            """CREATE TABLE IF NOT EXISTS wallets
                (wallet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL UNIQUE,
                balance BIGINT NOT NULL,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(user_id))"""
        )

    def create_wallet(self, user_id: int, address: str, init_balance: int) -> bool:
        try:
            self._cursor.execute(
                "INSERT INTO wallets (balance, address, user_id) VALUES (?, ?, ?)",
                (init_balance, address, user_id),
            )
        except IntegrityError:
            return False
        self.connection.commit()
        return self._cursor.rowcount == 1

    def get_wallet_id(self, address: str) -> int:
        self._cursor.execute(
            "SELECT wallet_id FROM wallets where address = ?",
            (address,),
        )
        row = self._cursor.fetchone()
        if row is None:
            return -1
        wallet_id: int = row[0]
        return wallet_id

    def get_user_wallets(self, user_id: int) -> List[int]:
        self._cursor.execute(
            "SELECT wallet_id FROM wallets where user_id = ?",
            (user_id,),
        )
        ids = self._cursor.fetchall()
        return list(sum(ids, ()))

    def check_wallet_validity(self, wallet_address: str) -> int:
        return self.get_wallet_id(address=wallet_address)

    def get_wallet_balance(self, address: str) -> int:
        self._cursor.execute(
            "SELECT balance FROM wallets where address = ?",
            (address,),
        )
        row = self._cursor.fetchone()
        if row is None:
            return -1
        satoshi_balance: int = row[0]
        return satoshi_balance

    def set_balance(self, address: str, amount: int) -> bool:
        self._cursor.execute(
            """UPDATE wallets
               SET balance = ?
               WHERE address = ?""",
            (amount, address),
        )

        row = self._cursor.fetchone()
        return row is not None
