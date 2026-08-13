import os
import time

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


def init_db(attempts: int = 10, retry_delay: float = 1.0) -> None:
    for attempt in range(attempts):
        try:
            with connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_xact_lock(734274)")
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS tasks (
                            id SERIAL PRIMARY KEY,
                            title TEXT NOT NULL,
                            done BOOLEAN NOT NULL DEFAULT FALSE
                        )
                        """
                    )
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS triage_jobs (
                            id UUID PRIMARY KEY,
                            idempotency_key TEXT NOT NULL UNIQUE,
                            request_hash TEXT NOT NULL,
                            input_text TEXT NOT NULL,
                            status TEXT NOT NULL DEFAULT 'queued'
                                CHECK (status IN ('queued', 'running', 'succeeded', 'failed')),
                            result JSONB,
                            error TEXT,
                            attempts INTEGER NOT NULL DEFAULT 0,
                            max_attempts INTEGER NOT NULL DEFAULT 3,
                            available_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                            lease_token UUID,
                            lease_expires_at TIMESTAMPTZ,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    )
                    cursor.execute(
                        """
                        CREATE INDEX IF NOT EXISTS triage_jobs_claim_idx
                        ON triage_jobs (available_at, created_at)
                        WHERE status IN ('queued', 'running')
                        """
                    )
                    cursor.execute("SELECT COUNT(*) FROM tasks")
                    if cursor.fetchone()[0] == 0:
                        cursor.executemany(
                            "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                            SEED_TASKS,
                        )
            return
        except psycopg.OperationalError:
            if attempt == attempts - 1:
                raise
            time.sleep(retry_delay)


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
