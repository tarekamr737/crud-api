# Task API

Task API is a small FastAPI CRUD service backed by PostgreSQL. Docker Compose
runs the API and database together, while a named volume keeps task data across
full-stack restarts.

![Task API Swagger UI](docs/swagger-ui.png)

## Start the stack

Docker with Compose is the only prerequisite. From a clean clone:

```bash
cp .env.example .env
docker compose up
```

Open Swagger UI at <http://127.0.0.1:8000/docs>. The API connects to the `db`
service, creates the `tasks` table automatically, and inserts three examples
only when the table is empty.

The environment file supplies these development settings:

| Variable | Purpose |
|---|---|
| `POSTGRES_USER` | PostgreSQL login used by the stack |
| `POSTGRES_PASSWORD` | PostgreSQL password used by the stack |
| `POSTGRES_DB` | Database created by the official PostgreSQL image |
| `DATABASE_URL` | Psycopg connection URL; its Compose host is `db` |

`.env.example` contains runnable local defaults. Copy it to the git-ignored
`.env` file before starting the stack; do not commit real credentials.

## Endpoints

| Method | Path | Purpose | Success |
|---|---|---|---|
| GET | `/` | Show API metadata | 200 |
| GET | `/health` | Check API health | 200 |
| GET | `/tasks` | List tasks | 200 |
| GET | `/tasks/{task_id}` | Get one task | 200 |
| POST | `/tasks` | Create a task | 201 |
| PUT | `/tasks/{task_id}` | Update a task | 200 |
| DELETE | `/tasks/{task_id}` | Delete a task | 204 |

Unknown task IDs return JSON `404` responses. Invalid POST or PUT bodies return
JSON `400` responses.

For example:

```bash
curl -i -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Ship containerized API"}'
```

The response is HTTP `201 Created` with the generated ID, title, and
`"done": false`.

## PostgreSQL proof

Inspect the same rows directly in the database container:

```bash
docker compose exec db psql -U tasks_user -d tasks \
  -c "SELECT id, title, done FROM tasks ORDER BY id;"
```

![PostgreSQL rows queried with psql](docs/postgres-psql.png)

The captured query returned the same three initial tasks exposed by
`GET /tasks`.

## Persistence

PostgreSQL stores its data in the Compose named volume `taskdata`. Create or
change tasks, then restart the entire stack:

```bash
docker compose down
docker compose up
```

The rows remain because `docker compose down` removes containers and the
network, but not the named volume. Use `docker compose down -v` only when you
intentionally want to delete local database data.
