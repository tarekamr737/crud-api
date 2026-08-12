# PRODUCT.md

# Task API — A3 Containerized Postgres Upgrade

## Goal
Move the existing A1/A2 Task API from SQLite to PostgreSQL running in Docker, then containerize the API so:

```bash
docker compose up
```

starts the whole stack.

## Storage evolution
```text
A1: FastAPI -> memory
A2: FastAPI -> SQLite
A3: FastAPI -> PostgreSQL in Docker
```

The client-visible API must not change.

## API contract
| Method | Path | Success |
|---|---|---|
| GET | `/` | 200 |
| GET | `/health` | 200 |
| GET | `/tasks` | 200 |
| GET | `/tasks/{id}` | 200 |
| POST | `/tasks` | 201 |
| PUT | `/tasks/{id}` | 200 |
| DELETE | `/tasks/{id}` | 204 |

Keep A1/A2 validation:
- missing/empty POST title -> 400
- invalid/empty PUT -> 400
- unknown ID -> 404 JSON
- DELETE success -> 204 empty body

## Database
Use `DATABASE_URL` from environment.

Schema:
```sql
CREATE TABLE IF NOT EXISTS tasks (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  done BOOLEAN NOT NULL DEFAULT FALSE
);
```

Startup:
1. connect
2. create table if missing
3. count rows
4. seed 3 examples only when empty

## CRUD SQL
```sql
SELECT id,title,done FROM tasks;
SELECT id,title,done FROM tasks WHERE id = %s;
INSERT INTO tasks (title,done) VALUES (%s,%s) RETURNING id,title,done;
UPDATE tasks SET title=%s, done=%s WHERE id=%s RETURNING id,title,done;
DELETE FROM tasks WHERE id=%s;
```

All request-derived values must be parameters.

## Docker
Postgres:
- official `postgres` image
- DB name `tasks`
- named volume
- environment-driven credentials

API:
- built from a small `Dockerfile`
- connects to host `db` inside Compose
- receives `DATABASE_URL`

Compose services:
```text
api
db
```

## Secrets
```text
.env          # local real values; never commit
.env.example  # committed template
```

## Persistence
Create tasks, run:
```bash
docker compose down
docker compose up
```
Tasks must remain.

## Delivery
Continue in the same public repo. README must include:
- what the stack is
- `.env.example` setup
- `docker compose up`
- env vars
- endpoint table
- one `curl -i`
- DB screenshot/psql proof
- persistence explanation

## Non-goals
No Kubernetes, Redis, cloud deployment, CI/CD, reverse proxy, TLS, auth, secrets manager, observability, or advanced DB tuning.

## Optional
Only after core acceptance:
- DB-aware `/health`
- index + `EXPLAIN ANALYZE`
- Redis
- multi-stage Dockerfile
- no-volume mortality experiment

## Acceptance
Postgres runs in Docker; whole stack starts with one Compose command; API contract unchanged; schema/seed auto-create; CRUD uses Postgres; SQL is parameterized; `.env` ignored and `.env.example` committed; data survives full-stack restart; clean clone works in under 5 minutes.
