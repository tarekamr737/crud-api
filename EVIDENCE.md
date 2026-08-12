# Evidence

## Stage 0 — SQLite initialization

- `python -m pytest tests/test_db.py -q` → `2 passed in 0.06s`.
- The focused tests create a fresh temporary database, inspect the `tasks` table and exact seed rows, then initialize the same database three times and assert the row count remains exactly 3.
- `python -m pytest tests/test_api.py -q` → `9 passed in 0.66s`, proving the A1 contract still passes after startup initialization was added.

## Stage 1 — Database read endpoints

- `python -m pytest tests/test_db.py tests/test_api.py::test_read_tasks_and_missing_task -q` → `4 passed in 0.57s`.
- The database read test changes a row through a separate SQLite connection and verifies `fetch_tasks`/`fetch_task` immediately return that state with integer `done` values converted to booleans.
- GET by ID uses `WHERE id = ?` with the route ID passed as a bound parameter; the existing endpoint test proves the 200 and JSON 404 responses are unchanged.
