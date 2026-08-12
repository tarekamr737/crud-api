import sqlite3

from app.db import SEED_TASKS, initialize_database


def test_initialize_creates_database_table_and_three_seed_rows(tmp_path) -> None:
    db_path = tmp_path / "tasks.db"

    initialize_database(db_path)

    assert db_path.exists()
    with sqlite3.connect(db_path) as connection:
        schema = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'tasks'"
        ).fetchone()
        rows = connection.execute(
            "SELECT id, title, done FROM tasks ORDER BY id"
        ).fetchall()

    assert schema is not None
    assert rows == list(SEED_TASKS)


def test_initialize_three_times_does_not_duplicate_seed_rows(tmp_path) -> None:
    db_path = tmp_path / "tasks.db"

    initialize_database(db_path)
    initialize_database(db_path)
    initialize_database(db_path)

    with sqlite3.connect(db_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

    assert count == 3
