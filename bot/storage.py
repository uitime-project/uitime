import sqlite3

class TokenStorage:
    def __init__(self, db_name="bot_sessions.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.execute("CREATE TABLE IF NOT EXISTS sessions (telegram_id INTEGER PRIMARY KEY, token TEXT)")
        self.conn.commit()

    def get(self, telegram_id: int):
        cur = self.conn.execute("SELECT token FROM sessions WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        return row[0] if row else None

    def set(self, telegram_id: int, token: str):
        self.conn.execute("INSERT OR REPLACE INTO sessions (telegram_id, token) VALUES (?, ?)", (telegram_id, token))
        self.conn.commit()

db = TokenStorage()