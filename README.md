# Task API with Supabase Auth

Task API is a FastAPI CRUD service backed by PostgreSQL and protected by
Supabase Auth. Supabase owns user accounts, passwords, sessions, and token
issuance; FastAPI verifies each protected request's Bearer token with Supabase.
The original task CRUD and PostgreSQL persistence behavior remain unchanged.

![Task API Swagger UI](docs/swagger-ui.png)

## Supabase setup

Create a Supabase project and copy its project URL and anon/publishable key from
the project's API settings. Never use a `service_role` key in this application.

Copy the environment template and replace only the Supabase placeholders with
your project's real values:

```bash
cp .env.example .env
```

```dotenv
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-publishable-key
```

The `.env` file is ignored by Git. Passwords are sent directly to Supabase Auth;
the API never stores or hashes them.

## Start the stack

Docker with Compose is the only prerequisite. From a clean clone:

```bash
docker compose up --build
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
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon/publishable key; never `service_role` |

`.env.example` contains runnable PostgreSQL defaults and safe Supabase
placeholders. Copy it to the git-ignored `.env` file, add real Supabase values,
and never commit those credentials.

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
| POST | `/auth/signup` | Create a Supabase user | 201 |
| POST | `/auth/login` | Return access and refresh tokens | 200 |
| POST | `/auth/logout` | Sign out the authenticated user | 204 |
| GET | `/public/info` | Read public information | 200 |
| GET | `/protected/profile` | Read safe authenticated-user data | 200 |
| GET | `/protected/dashboard` | Read a second protected resource | 200 |

Unknown task IDs return JSON `404` responses. Invalid POST or PUT bodies return
JSON `400` responses.

Signup and login require non-empty `email` and `password` JSON fields. Invalid
login credentials return JSON `401`. Protected routes require exactly:

```http
Authorization: Bearer <access_token>
```

Missing, malformed, invalid, tampered, or expired tokens return JSON `401`.
Signup behavior depends on the project's **Confirm email** setting: when it is
enabled, confirm the email before logging in.

## Authentication flow

1. `POST /auth/signup` with an email and password.
2. `POST /auth/login` and copy `access_token` from the response.
3. Open <http://127.0.0.1:8000/docs>, select **Authorize**, and paste only the
   access token into the HTTP Bearer field.
4. Call `/protected/profile` or `/protected/dashboard`; protected operations
   show lock icons in Swagger UI.
5. Call `POST /auth/logout` with the same Bearer authentication.

Example login:

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"person@example.com","password":"your-password"}'
```

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
