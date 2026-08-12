import os

import psycopg


DATABASE_URL = os.environ["DATABASE_URL"]
SEED_TASKS = (
    ("Buy milk", False),
    ("Write report", True),
    ("Call dentist", False),
)


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
