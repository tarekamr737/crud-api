import os

import psycopg
from typing_extensions import TypedDict


DATABASE_URL = os.environ["DATABASE_URL"]
SEED_TASKS = (
    ("Buy milk", False),
    ("Write report", True),
    ("Call dentist", False),
)


class Task(TypedDict):
    id: int
    title: str
    done: bool


def connect() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL)


def init_db() -> None:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE
                )
                """
            )
            cursor.execute("SELECT COUNT(*) FROM tasks")
            if cursor.fetchone()[0] == 0:
                cursor.executemany(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                    SEED_TASKS,
                )


def row_to_task(row: tuple[int, str, bool]) -> Task:
    return {"id": row[0], "title": row[1], "done": row[2]}


def list_tasks() -> list[Task]:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, title, done FROM tasks ORDER BY id")
            rows = cursor.fetchall()
    return [row_to_task(row) for row in rows]


def get_task(task_id: int) -> Task | None:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, done FROM tasks WHERE id = %s", (task_id,)
            )
            row = cursor.fetchone()
    return row_to_task(row) if row is not None else None


def create_task(title: str) -> Task:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tasks (title, done)
                VALUES (%s, %s)
                RETURNING id, title, done
                """,
                (title, False),
            )
            row = cursor.fetchone()
    return row_to_task(row)


def update_task(task_id: int, title: str | None, done: bool | None) -> Task | None:
    current = get_task(task_id)
    if current is None:
        return None

    updated_title = title if title is not None else current["title"]
    updated_done = done if done is not None else current["done"]
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE tasks
                SET title = %s, done = %s
                WHERE id = %s
                RETURNING id, title, done
                """,
                (updated_title, updated_done, task_id),
            )
            row = cursor.fetchone()
    return row_to_task(row)


def delete_task(task_id: int) -> bool:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            return cursor.rowcount > 0
