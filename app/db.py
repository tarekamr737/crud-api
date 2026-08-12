import sqlite3
from pathlib import Path

from typing_extensions import TypedDict


DB_PATH = Path(__file__).resolve().parent.parent / "tasks.db"
SEED_TASKS = (
    (1, "Buy milk", 0),
    (2, "Write report", 1),
    (3, "Call dentist", 0),
)


class Task(TypedDict):
    id: int
    title: str
    done: bool


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def row_to_task(row: sqlite3.Row) -> Task:
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


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


def fetch_tasks(db_path: Path = DB_PATH) -> list[Task]:
    with get_connection(db_path) as connection:
        rows = connection.execute("SELECT id, title, done FROM tasks").fetchall()
    return [row_to_task(row) for row in rows]


def fetch_task(task_id: int, db_path: Path = DB_PATH) -> Task | None:
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return row_to_task(row) if row is not None else None
