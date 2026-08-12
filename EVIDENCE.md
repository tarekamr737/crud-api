# Evidence

## A3 Stage 0 — PostgreSQL in Docker

- `docker volume create crud-api-taskdata` created the named persistence volume.
- `docker run ... postgres:17-alpine` started the official PostgreSQL image as `crud-api-postgres`, mounting `crud-api-taskdata` at `/var/lib/postgresql/data`.
- `docker exec crud-api-postgres psql -U tasks_user -d tasks -c "SELECT current_database(), current_user;"` returned database `tasks` and user `tasks_user`.
- `git check-ignore .env` confirms local credentials are excluded from Git.

## Stage 0 — SQLite initialization

- `python -m pytest tests/test_db.py -q` → `2 passed in 0.06s`.
- The focused tests create a fresh temporary database, inspect the `tasks` table and exact seed rows, then initialize the same database three times and assert the row count remains exactly 3.
- `python -m pytest tests/test_api.py -q` → `9 passed in 0.66s`, proving the A1 contract still passes after startup initialization was added.

## Stage 1 — Database read endpoints

- `python -m pytest tests/test_db.py tests/test_api.py::test_read_tasks_and_missing_task -q` → `4 passed in 0.57s`.
- The database read test changes a row through a separate SQLite connection and verifies `fetch_tasks`/`fetch_task` immediately return that state with integer `done` values converted to booleans.
- GET by ID uses `WHERE id = ?` with the route ID passed as a bound parameter; the existing endpoint test proves the 200 and JSON 404 responses are unchanged.

## Stage 2 — Database inserts

- `python -m pytest tests/test_db.py tests/test_api.py::test_create_rejects_invalid_bodies tests/test_api.py::test_create_assigns_next_id_and_updates_state -q` → `9 passed in 0.55s`.
- The focused persistence test inserts `Ship API`, reinitializes the database to simulate a restart, then reads ID 4 from a fresh connection and gets the same task.
- POST continues to return 201, invalid bodies return the unchanged JSON 400, and both the title and generated ID are handled through parameterized SQL/SQLite `lastrowid`.

## Stage 3 — Database updates and deletes

- `python -m pytest -q` → `14 passed in 0.66s`.
- The database test updates task 1, deletes task 2, reinitializes the database to simulate a restart, and proves the updated row remains while the deleted row remains absent.
- The unchanged A1 endpoint assertions prove invalid PUT bodies return JSON 400, unknown IDs return JSON 404, and successful DELETE returns 204 with an empty body.
- UPDATE binds title, boolean, and ID through `?` placeholders; DELETE binds its ID through a `?` placeholder. The application no longer contains an in-memory task list.

## Stage 4 — SQLite exploration

- Installed DB Browser for SQLite 3.13.1 and opened the repository-root `tasks.db` with `docs/stage4.sql`.
- Ran all five required statements. `SELECT COUNT(*) FROM tasks;` returned 3 before the destructive statements: the three seeded tasks.
- After `UPDATE tasks SET done = 1;` followed by `DELETE FROM tasks WHERE done = 1;`, an independent SQLite connection reported `after_required_sql_count=0`, proving DB Browser executed the changes.
- Restored the validated pre-exploration backup; a fresh connection returned `[(1, 'Buy milk', 0), (2, 'Write report', 1), (3, 'Call dentist', 0)]`.

## Stage 5 — Documentation and clean bootstrap

- Moved the existing runtime database aside, ran `python -c "import app.main"`, and confirmed a new repository-root `tasks.db` was created automatically.
- Direct inspection returned exactly `[(1, 'Buy milk', 0), (2, 'Write report', 1), (3, 'Call dentist', 0)]` and columns `id INTEGER PRIMARY KEY`, `title TEXT NOT NULL`, `done INTEGER NOT NULL DEFAULT 0`.
- `python -m pytest -q` → `14 passed in 0.55s` after the documentation changes.
- Captured and visually checked `docs/db-browser.png`; it shows DB Browser for SQLite open on `tasks.db` with the `tasks` table and required schema.

## Test — Full regression and SQL safety

- `python -m pytest -q` → `15 passed in 0.58s`.
- Added an integration test that creates, updates, and deletes through the API while checking the corresponding row directly through a separate SQLite connection after each operation.
- Audited every `SELECT`, `INSERT`, `UPDATE`, and `DELETE` in `app/db.py`. Every request-derived ID, title, and boolean is supplied as a bound argument to a `?` placeholder; no SQL uses interpolation or concatenation.
- Searched `app/` for list assignment/append/remove patterns and found no in-memory task collection.

## Final — Clean clone, restart, and database agreement

- Cloned the committed repository into a new temporary directory and confirmed it contained no `tasks.db`.
- Started it with the README's exact `python -m uvicorn app.main:app --reload` command; health passed and the newly created database contained 3 seeds.
- POST created `{"id":4,"title":"Restart survivor","done":false}`, PUT changed `done` to true, and DELETE of task 1 returned 204.
- Before and after a complete server stop/restart, GET `/tasks` returned the identical state: tasks 2, 3, and 4 with task 4 still done.
- DB Browser ran `docs/final-verify.sql` against that clone with exit code 0. A separate SQLite connection returned `[[2, "Write report", 1], [3, "Call dentist", 0], [4, "Restart survivor", 1]]`, exactly matching the API after boolean conversion.
- Stopped both server process trees and removed the validated temporary clone.

## Push — Public repository delivery

- `git push origin main` updated `https://github.com/tarekamr737/crud-api.git` from `afddfc4` to `3121075`.
- `git ls-remote origin refs/heads/main` returned `3121075aa57e852b81d9cb14caee15f9df05213c`, matching the local FINAL commit before the delivery bookkeeping commit.
- Verified the history contains the required Stage 0 through Stage 5 commit messages followed by dedicated TEST and FINAL commits.
