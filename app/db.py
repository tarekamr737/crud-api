import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "tasks.db"
SEED_TASKS = (
    (1, "Buy milk", 0),
    (2, "Write report", 1),
    (3, "Call dentist", 0),
)


def initialize_database(db_path: Path = DB_PATH) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        row_count = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if row_count == 0:
            connection.executemany(
                "INSERT INTO tasks (id, title, done) VALUES (?, ?, ?)",
                SEED_TASKS,
            )
        connection.commit()
