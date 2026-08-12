# Evidence

## A4 Baseline — Existing CRUD inspection

- `app/main.py` exposes the existing `/`, `/health`, `/tasks`, and `/tasks/{task_id}` contracts and delegates all persistence to `app/repository.py`.
- `app/repository.py` remains the sole PostgreSQL layer and uses bound `%s` parameters for request-derived values.
- The existing suite contains 16 CRUD/database regression tests covering validation, status codes, persistence, and OpenAPI paths.
- `.env` is ignored by `.gitignore` and absent from `git ls-files`; `.env.example` is tracked.

## A4 Stage 0 — Supabase client setup

- Installed and imported `supabase` 2.31.0 from the repository-local `.venv` on `D:`; `requirements.txt` bounds the supported major version to `<3.0`.
- `.env.example` now includes placeholder `SUPABASE_URL` and `SUPABASE_KEY` values while preserving the runnable PostgreSQL settings.
- A focused configuration check created the client from only those two variables and returned `configured`; a clean process without them returned the stable startup error `Missing required environment variable: SUPABASE_URL`.
- `git check-ignore -v .env` matched `.gitignore`, `git ls-files .env.example` found the template, and `git ls-files --error-unmatch .env` confirmed the real file is untracked.

## A4 Stage 1 — Signup and login

- `.venv\Scripts\python.exe -m pytest tests\test_auth.py -q` returned `6 passed`.
- Signup tests prove HTTP 201 returns only `id`, `email`, and `created_at`; missing/blank fields and provider failures return stable JSON 400 responses without provider details.
- Login tests prove HTTP 200 returns access and refresh tokens; missing/blank fields return JSON 400 and rejected credentials return stable JSON 401 without provider details.
- The request model passes passwords directly to Supabase and no application code stores, hashes, signs, or logs credentials or tokens.

## A4 Stage 2 — Public and protected routes

- `.venv\Scripts\python.exe -m pytest tests\test_auth.py tests\test_auth_dependency.py -q` returned `13 passed`.
- `/public/info` returns the exact required message with HTTP 200 and no authentication header.
- The reusable `HTTPBearer` dependency rejects missing, non-Bearer, empty, whitespace-containing, invalid, and expired/tampered credentials with stable JSON 401 responses and a `WWW-Authenticate: Bearer` header.
- A valid token is passed unchanged to `supabase.auth.get_user(token)`; the verified user then reaches both `/protected/profile` and `/protected/dashboard` through the same dependency.
- Profile output is limited to `id`, `email`, and `created_at`; the dashboard exposes only a message and verified user ID.

## A4 Stage 3 — Logout and Swagger Bearer auth

- `.venv\Scripts\python.exe -m pytest tests\test_auth.py tests\test_auth_dependency.py -q` returned `17 passed`.
- Logout first verifies the user with `get_user(token)`, then passes the same explicit user JWT to Supabase logout and returns HTTP 204 with an empty body; a missing token returns 401 before logout is called.
- Token cases explicitly cover valid, missing, Basic/non-Bearer, empty Bearer, whitespace-malformed, expired, and tampered values.
- The generated OpenAPI schema defines `HTTPBearer` as an HTTP bearer scheme, attaches it to both protected reads and logout, and leaves public info, signup, and login unlocked.

## A3 Stage 0 — PostgreSQL in Docker

- `docker volume create crud-api-taskdata` created the named persistence volume.
- `docker run ... postgres:17-alpine` started the official PostgreSQL image as `crud-api-postgres`, mounting `crud-api-taskdata` at `/var/lib/postgresql/data`.
- `docker exec crud-api-postgres psql -U tasks_user -d tasks -c "SELECT current_database(), current_user;"` returned database `tasks` and user `tasks_user`.
- `git check-ignore .env` confirms local credentials are excluded from Git.

## A3 Stage 1 — Environment connection, schema, and seeds

- Installed `psycopg[binary]` 3.3.4 and added its bounded requirement.
- Ran three separate `python -c "import app.main"` startups with `DATABASE_URL=postgresql://tasks_user:tasks_password@localhost:5432/tasks`; all exited 0.
- Direct `psql` inspection after the third startup showed the required `SERIAL`/`TEXT`/`BOOLEAN` schema and exactly 3 rows: `Buy milk` false, `Write report` true, and `Call dentist` false.
- `python -m pytest -q` with the PostgreSQL URL set returned `15 passed in 0.78s`, preserving the existing contract during this staged initialization change.
- `.env` contains the local host URL and is ignored; committed `.env.example` contains the Compose service host `db`.

## A3 Stage 2 — PostgreSQL reads

- `python -m pytest tests/test_api.py::test_read_tasks_and_missing_task -q` with the PostgreSQL URL set returned `1 passed in 0.62s`.
- The unchanged endpoint assertions received the three PostgreSQL seed rows with HTTP 200, received task 2 by ID with HTTP 200, and retained the JSON HTTP 404 response for ID 99.
- `app/repository.py` binds the route ID with `WHERE id = %s` and `(task_id,)`; routes contain no SQL.

## A3 Stage 3 — Full PostgreSQL CRUD

- `python -m pytest -q` with the PostgreSQL URL set returned `16 passed in 2.68s`.
- The preserved API tests prove POST 201, PUT 200, DELETE 204 with an empty body, invalid POST/PUT 400 JSON, and missing-resource 404 JSON behavior.
- Repository tests create ID 4, update task 1, delete task 2, call database initialization again, and confirm all mutations remain in PostgreSQL.
- The API/database integration test verifies created, updated, and deleted state through a separate PostgreSQL connection after each HTTP mutation.
- A source audit found no SQLite import or route SQL. Every request-derived title, boolean, and ID is passed separately to a `%s` placeholder in `app/repository.py`.

## A3 Stage 4 — Full Compose stack

- `docker compose config` resolved exactly two services, `api` and `db`, and the API URL to `postgresql://tasks_user:tasks_password@db:5432/tasks`.
- `docker compose up --build -d` built the minimal Python image, started both containers, and created the named `connectingcrudtothedatabase_taskdata` volume.
- `docker compose ps` reported both services `Up`; direct inspection inside the API container confirmed its database host is `db`.
- `GET http://127.0.0.1:8000/tasks` returned HTTP 200 and the three seed tasks; `psql` in the Compose DB container independently returned `task_count = 3`.
- `python -m pytest -q` returned `16 passed in 3.17s` after the bounded startup retry and container files were added.

## A3 Stage 5 — Documentation and clean clone

- README now documents the FastAPI/PostgreSQL stack, `cp .env.example .env`, `docker compose up`, all four environment variables, every endpoint, a `curl -i` POST, direct `psql` inspection, and named-volume persistence.
- Captured and visually inspected `docs/postgres-psql.png`; it clearly shows the verified direct query and all three seed rows.
- Exported the staged Git tree into a new directory with no `.env`, copied `.env.example` to `.env`, and ran the documented `docker compose up --build -d` flow successfully.
- The clean snapshot reported both services `Up`, `GET /tasks` returned HTTP 200 with exactly three seeds, and direct `psql` returned the identical rows.
- Removed only the disposable clean-clone containers, network, volume, and verified temporary directory after the check passed.

## A3 Test — Contract, SQL safety, and secrets

- `python -m pytest -q` against PostgreSQL returned `16 passed in 2.66s`, covering all A1/A2 endpoint behavior plus schema, idempotent seed, persistence, and direct database agreement.
- Enumerated every `execute`/`executemany` call in `app/repository.py`; an AST check returned `interpolated_sql_calls=[]`, proving no SQL argument is an f-string or concatenated expression.
- `rg` found no SQL statement in `app/main.py`, so routes remain storage-agnostic.
- `git check-ignore -v .env` matched `.gitignore`; `git ls-files --error-unmatch .env` confirmed it is absent from Git, while `git ls-files .env.example` confirmed the template is tracked.

## A3 Final — Full-stack restart persistence

- Started the main Compose project on its preserved `taskdata` volume and created `Restart survivor one` (ID 4) and `Restart survivor two` (ID 5) through POST `/tasks`.
- Ran `docker compose down` followed by `docker compose up -d`, recreating both containers and their network without deleting the named volume.
- After restart, GET `/tasks` returned HTTP 200 with all five rows, including both new tasks under their original IDs.
- Direct `psql` returned the same five IDs, titles, and boolean values in order; `docker compose ps` reported both recreated services `Up`.

## A3 Push — Public repository delivery

- `git push origin main` updated `https://github.com/tarekamr737/crud-api.git` from `cdf8737` to `ed9a4ca`.
- `git ls-remote origin refs/heads/main` returned `ed9a4cadbeb8b85503c5380723f809b7099dd12f`, exactly matching the local FINAL commit before this delivery bookkeeping commit.
- Audited the linear history and confirmed the required Stage 0 through Stage 5 messages, followed by dedicated TEST and FINAL commits; each stage was committed only after its recorded checkpoint passed.

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
