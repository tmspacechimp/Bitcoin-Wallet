from sqlite3 import Connection, Cursor


class UsersSqlRepository:
    connection: Connection
    _cursor: Cursor

    def __init__(self, connection: Connection) -> None:
        self.connection = connection
        self._cursor = connection.cursor()
        self._cursor.execute(
            """CREATE TABLE IF NOT EXISTS users
                (user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                api_key TEXT NOT NULL UNIQUE)"""
        )

    def create_user(self, email: str, api_key: str) -> bool:
        self._cursor.execute(
            "INSERT INTO users (email, api_key) VALUES (?, ?)",
            (email, api_key),
        )
        self.connection.commit()
        return self._cursor.rowcount == 1

    def user_exists_with_email(self, email: str) -> bool:
        self._cursor.execute(
            "SELECT user_id FROM users where email = ?",
            (email,),
        )
        row = self._cursor.fetchone()
        if row is None:
            return False
        return True

    def get_user_id(self, api_key: str) -> int:
        self._cursor.execute(
            "SELECT user_id FROM users where api_key = ?",
            (api_key,),
        )
        row = self._cursor.fetchone()
        if row is None:
            return -1
        user_id: int = row[0]
        return user_id
