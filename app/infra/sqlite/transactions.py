from sqlite3 import Connection, Cursor
from typing import List, Tuple

from app.core.models.resp.transaction import TransactionResponse


class TransactionSqlRepository:
    connection: Connection
    _cursor: Cursor

    def __init__(self, connection: Connection) -> None:
        self.connection = connection
        self._cursor = connection.cursor()
        self._cursor.execute(
            """CREATE TABLE IF NOT EXISTS transactions
                (transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_id INTEGER,
                to_id INTEGER,
                amount BIGINT,
                commission BIGINT,
                FOREIGN KEY (from_id) REFERENCES wallets(wallet_id),
                FOREIGN KEY (to_id) REFERENCES wallets(wallet_id))"""
        )

    def check_transaction_validity(self, from_id: int, to_id: int) -> bool:
        self._cursor.execute(
            "SELECT * FROM wallets WHERE wallet_address = ? OR wallet_address = ?",
            (from_id, to_id),
        )
        return self._cursor.rowcount == 2

    def create_transaction(
        self, from_id: int, to_id: int, amount: int, commission_satoshi: int
    ) -> bool:
        self._cursor.execute(
            """INSERT INTO transactions (from_id, to_id, amount, commission)
            VALUES (?, ?, ?, ?)""",
            (from_id, to_id, amount, commission_satoshi),
        )
        self.connection.commit()
        return self._cursor.rowcount == 1

    def get_transactions(self, wallet_ids: List[int]) -> List[TransactionResponse]:
        # wallet_tuples = [wallet_ids[i] for i in range(len(wallet_ids))]
        # wallet_tuples = (1, 2, 3)
        # self._cursor.execute(
        #     "SELECT * FROM transactions WHERE from_id in ?", (wallet_ids,)
        # )
        query = """SELECT w1.address, w2.address, t.amount
                FROM transactions t
                INNER JOIN wallets w1 ON t.from_id == w1.wallet_id
                INNER JOIN wallets w2 ON t.to_id == w2.wallet_id
                WHERE t.from_id in ({}) OR t.to_id in ({})""".format(
            ",".join("?" for x in wallet_ids), ",".join("?" for x in wallet_ids)
        )
        self._cursor.execute(query, wallet_ids + wallet_ids)
        rows = self._cursor.fetchall()
        answer: List[TransactionResponse] = [
            TransactionResponse(row[0], row[1], row[2]) for row in rows
        ]
        return answer

    def get_statistics(self) -> Tuple[int, int]:
        self._cursor.execute("SELECT count(*), sum(commission) FROM transactions")
        row = self._cursor.fetchone()
        if row[0] == 0:
            return 0, 0
        total_count: int = row[0]
        total_profit: int = row[1]
        return total_count, total_profit
