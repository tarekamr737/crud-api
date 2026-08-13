import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repository import SEED_TASKS as DB_SEED_TASKS, connect


SEED_TASKS = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Write report", "done": True},
    {"id": 3, "title": "Call dentist", "done": False},
]

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_tasks() -> None:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE tasks RESTART IDENTITY")
            cursor.executemany(
                "INSERT INTO tasks (title, done) VALUES (%s, %s)", DB_SEED_TASKS
            )


def test_root_and_health() -> None:
    root = client.get("/")
    health = client.get("/health")

    assert root.status_code == 200
    assert root.json() == {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks", "/triage", "/triage/jobs/{job_id}"],
    }
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}


def test_read_tasks_and_missing_task() -> None:
    listed = client.get("/tasks")
    found = client.get("/tasks/2")
    missing = client.get("/tasks/99")

    assert listed.status_code == 200
    assert listed.json() == SEED_TASKS
    assert found.status_code == 200
    assert found.json() == SEED_TASKS[1]
    assert missing.status_code == 404
    assert missing.json() == {"error": "Task 99 not found"}


@pytest.mark.parametrize(
    "body",
    [{}, {"title": ""}, {"title": "   "}, None],
)
def test_create_rejects_invalid_bodies(body: object) -> None:
    response = client.post("/tasks", json=body)

    assert response.status_code == 400
    assert response.json() == {"error": "Invalid request"}


def test_create_assigns_next_id_and_updates_state() -> None:
    response = client.post("/tasks", json={"title": "Ship API"})

    assert response.status_code == 201
    assert response.json() == {"id": 4, "title": "Ship API", "done": False}
    assert client.get("/tasks/4").json() == response.json()


def test_update_delete_and_missing_behavior() -> None:
    created = client.post("/tasks", json={"title": "CRUD target"}).json()
    task_id = created["id"]

    updated = client.put(
        f"/tasks/{task_id}",
        json={"title": "CRUD complete", "done": True},
    )
    assert updated.status_code == 200
    assert updated.json() == {
        "id": task_id,
        "title": "CRUD complete",
        "done": True,
    }

    assert client.put(f"/tasks/{task_id}", json={}).status_code == 400
    assert client.put(f"/tasks/{task_id}", json={"title": ""}).status_code == 400
    assert client.put("/tasks/99", json={"done": True}).status_code == 404
    assert client.delete("/tasks/99").status_code == 404

    deleted = client.delete(f"/tasks/{task_id}")
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(f"/tasks/{task_id}").status_code == 404


def test_api_mutations_match_database_rows() -> None:
    created = client.post("/tasks", json={"title": "Database truth"}).json()

    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, done FROM tasks WHERE id = %s", (created["id"],)
            )
            row = cursor.fetchone()
    assert row == (created["id"], "Database truth", False)

    client.put(f"/tasks/{created['id']}", json={"done": True})
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT done FROM tasks WHERE id = %s", (created["id"],))
            done = cursor.fetchone()[0]
    assert done is True

    client.delete(f"/tasks/{created['id']}")
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM tasks WHERE id = %s", (created["id"],))
            missing = cursor.fetchone()
    assert missing is None


def test_openapi_contains_every_endpoint() -> None:
    response = client.get("/openapi.json")
    paths = response.json()["paths"]

    assert response.status_code == 200
    assert {"/", "/health", "/tasks", "/tasks/{task_id}"} <= paths.keys()
    assert {"get", "post"} <= paths["/tasks"].keys()
    assert {"get", "put", "delete"} <= paths["/tasks/{task_id}"].keys()

