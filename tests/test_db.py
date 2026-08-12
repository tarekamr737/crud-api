import pytest

from app.repository import (
    SEED_TASKS,
    connect,
    create_task,
    delete_task,
    get_task,
    init_db,
    list_tasks,
    update_task,
)


@pytest.fixture(autouse=True)
def reset_tasks() -> None:
    init_db()
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE tasks RESTART IDENTITY")
    init_db()


def test_initialize_creates_table_and_three_seed_rows() -> None:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE tasks")

    init_db()

    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.tasks')")
            table = cursor.fetchone()[0]
            cursor.execute("SELECT id, title, done FROM tasks ORDER BY id")
            rows = cursor.fetchall()

    assert table == "tasks"
    assert rows == [
        (1, "Buy milk", False),
        (2, "Write report", True),
        (3, "Call dentist", False),
    ]


def test_initialize_three_times_does_not_duplicate_seed_rows() -> None:
    init_db()
    init_db()
    init_db()

    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM tasks")
            count = cursor.fetchone()[0]

    assert count == 3


def test_list_and_get_read_current_database_state() -> None:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE tasks SET done = %s WHERE id = %s", (True, 1))

    assert list_tasks() == [
        {"id": 1, "title": "Buy milk", "done": True},
        {"id": 2, "title": "Write report", "done": True},
        {"id": 3, "title": "Call dentist", "done": False},
    ]
    assert get_task(1) == {"id": 1, "title": "Buy milk", "done": True}
    assert get_task(99) is None


def test_create_uses_postgres_id_and_persists() -> None:
    created = create_task("Ship API")
    init_db()

    assert created == {"id": 4, "title": "Ship API", "done": False}
    assert get_task(4) == created


def test_update_and_delete_persist_after_reinitialization() -> None:
    updated = update_task(1, "Buy oat milk", True)

    assert updated == {"id": 1, "title": "Buy oat milk", "done": True}
    assert update_task(99, None, True) is None
    assert delete_task(2) is True
    assert delete_task(99) is False

    init_db()
    assert get_task(1) == updated
    assert get_task(2) is None


def test_seed_definition_remains_exactly_three_examples() -> None:
    assert SEED_TASKS == (
        ("Buy milk", False),
        ("Write report", True),
        ("Call dentist", False),
    )
