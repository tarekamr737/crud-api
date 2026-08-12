# ARCHITECTURE.md

## Stack
- Python 3.10+
- FastAPI + Uvicorn + Pydantic
- PostgreSQL
- `psycopg[binary]`
- Docker + Docker Compose
- pytest / FastAPI TestClient

## Keep structure minimal
```text
app/
  main.py
  repository.py
tests/
Dockerfile
compose.yaml
.env
.env.example
.gitignore
.dockerignore
requirements.txt
README.md
```

Do not reorganize working A2 code just to match this tree.

## Rule
```text
HTTP -> FastAPI routes -> repository.py -> psycopg -> PostgreSQL
```
Only repository code talks to the DB.

## Config
```python
DATABASE_URL = os.environ["DATABASE_URL"]
```

Local host may be `localhost`; inside Compose API must use host `db`.

## Repository responsibilities
Prefer small functions:
```text
connect
init_db
seed_if_empty
list_tasks
get_task
create_task
update_task
delete_task
```

## Connection
Use context-managed psycopg connections/cursors.

## Schema
```sql
CREATE TABLE IF NOT EXISTS tasks (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  done BOOLEAN NOT NULL DEFAULT FALSE
);
```

Seed only when `SELECT COUNT(*) FROM tasks` is zero.

## Parameterization
Correct:
```python
cur.execute("SELECT id,title,done FROM tasks WHERE id=%s", (task_id,))
```

Forbidden:
```python
cur.execute(f"SELECT * FROM tasks WHERE id={task_id}")
```

## Route mapping
GET list -> SELECT all.
GET one -> SELECT by id.
POST -> INSERT ... RETURNING.
PUT -> fetch existing, merge supplied fields, UPDATE ... RETURNING.
DELETE -> parameterized DELETE; missing -> 404; success -> 204.

## Dockerfile
Keep minimal: Python base -> workdir -> install requirements -> copy app -> run Uvicorn on `0.0.0.0`.

## Compose
Two services:
- `api`: build repo, expose app port, inject `DATABASE_URL`, depends on `db`
- `db`: official postgres image, env config, named volume `taskdata`

## Startup reliability
`depends_on` is not DB readiness. Use the smallest reliable option:
- tiny connection retry, or
- DB healthcheck + conditional dependency.

Do not add a large retry framework.

## Testing
Keep A1/A2 contract tests unchanged where possible. Add checks for:
- schema auto-create
- seed exactly once
- CRUD against Postgres
- full-stack persistence
- `.env` not tracked
- direct DB rows match API

## Git hygiene
`.gitignore`:
```gitignore
.env
.venv/
__pycache__/
.pytest_cache/
```

`.dockerignore`:
```text
.git
.env
.venv
__pycache__
.pytest_cache
tasks.db
```

## Clean-clone acceptance
```bash
cp .env.example .env
docker compose up
```
must yield a running API, running Postgres, auto-created table, 3 seed rows, and unchanged CRUD behavior.
