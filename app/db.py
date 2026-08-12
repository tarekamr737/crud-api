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


def insert_task(title: str, db_path: Path = DB_PATH) -> Task:
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)", (title, 0)
        )
        task_id = cursor.lastrowid
        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        connection.commit()
    return row_to_task(row)


def update_task_record(
    task_id: int,
    title: str | None,
    done: bool | None,
    db_path: Path = DB_PATH,
) -> Task | None:
    current = fetch_task(task_id, db_path)
    if current is None:
        return None

    updated_title = title if title is not None else current["title"]
    updated_done = done if done is not None else current["done"]
    with get_connection(db_path) as connection:
        connection.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (updated_title, int(updated_done), task_id),
        )
        connection.commit()
    return fetch_task(task_id, db_path)


def delete_task_record(task_id: int, db_path: Path = DB_PATH) -> bool:
    with get_connection(db_path) as connection:
        cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        connection.commit()
    return cursor.rowcount > 0
