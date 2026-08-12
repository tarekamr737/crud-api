import sqlite3

from app.db import SEED_TASKS, fetch_task, fetch_tasks, initialize_database


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


def test_fetch_tasks_reads_current_database_state(tmp_path) -> None:
    db_path = tmp_path / "tasks.db"
    initialize_database(db_path)

    with sqlite3.connect(db_path) as connection:
        connection.execute("UPDATE tasks SET done = ? WHERE id = ?", (1, 1))
        connection.commit()

    assert fetch_tasks(db_path) == [
        {"id": 1, "title": "Buy milk", "done": True},
        {"id": 2, "title": "Write report", "done": True},
        {"id": 3, "title": "Call dentist", "done": False},
    ]
    assert fetch_task(1, db_path) == {
        "id": 1,
        "title": "Buy milk",
        "done": True,
    }
    assert fetch_task(99, db_path) is None
