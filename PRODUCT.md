# PRODUCT.md

# Task API — Week 3 SQLite Upgrade

## Goal
Upgrade the existing Assignment 1 Task API so tasks are stored in SQLite
instead of an in-memory Python list.

The client-visible API must remain the same; only persistence changes.

## Core outcome
Before:
```text
Client -> FastAPI -> in-memory list
```

After:
```text
Client -> FastAPI -> SQLite (`tasks.db`)
```

Data must survive server restarts.

## Existing API contract — DO NOT CHANGE

| Method | Path | Behavior | Success |
|---|---|---|---|
| GET | `/` | API metadata | 200 |
| GET | `/health` | Health status | 200 |
| GET | `/tasks` | List tasks | 200 |
| GET | `/tasks/{id}` | Get one task | 200 |
| POST | `/tasks` | Create task | 201 |
| PUT | `/tasks/{id}` | Update task | 200 |
| DELETE | `/tasks/{id}` | Delete task | 204 |

Task response:
```json
{"id":1,"title":"Buy milk","done":false}
```

Carry forward A1 validation:
- missing/empty title on POST -> 400
- invalid/empty PUT body -> 400
- unknown ID -> 404 JSON error
- DELETE success -> 204 with empty body

## Database requirements
Database file:
```text
tasks.db
```

Schema:
```sql
CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  done INTEGER NOT NULL DEFAULT 0
);
```

Startup behavior:
1. create/open `tasks.db`
2. create `tasks` table if missing
3. count rows
4. insert 3 example tasks only when count is 0

Restarting repeatedly must never multiply seed rows.

## CRUD persistence
- GET reads with SQL
- POST inserts with SQL and lets SQLite assign ID
- PUT updates with SQL
- DELETE deletes with SQL
- all values derived from requests use parameterized placeholders
- created/updated/deleted state survives restart

## Manual SQL learning requirement
Using DB Browser for SQLite, run:
```sql
SELECT * FROM tasks;
SELECT * FROM tasks WHERE done = 1;
SELECT COUNT(*) FROM tasks;
UPDATE tasks SET done = 1;
DELETE FROM tasks WHERE done = 1;
```

README must include one query and one sentence describing its result.

## Delivery
Continue in the same public GitHub repo from A1.

README update must include:
- why SQLite was chosen
- where `tasks.db` lives
- that DB/table are auto-created
- one documented start command
- DB Browser screenshot
- one SQL query from Stage 4

A clean clone must run with no manual DB setup.

## Non-goals
No Postgres, ORM migration system, auth, frontend, Docker, cloud deployment,
microservices, Redis, async DB stack, or schema expansion unless optional work
is explicitly started later.

## Optional extras
Only after required acceptance passes:
- SQL search with `LIKE`
- filter by `done`
- `ORDER BY title`
- SQL-powered `/stats`
- timestamps
- index
- transaction for multi-row seed

## Acceptance
- same CRUD API contract as A1
- SQLite is the source of truth
- DB/table auto-create
- exactly 3 seed rows on first empty DB
- persistence survives restart
- all request-derived SQL values are parameterized
- required 200/201/204/400/404 behavior preserved
- A1 endpoint tests still pass
