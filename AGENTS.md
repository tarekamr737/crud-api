# AGENTS.md

## Mission
Upgrade the existing A1/A2 FastAPI Task API from SQLite to PostgreSQL in Docker, then run API + DB together with one `docker compose up`.

## Read order
1. `PRODUCT.md`
2. `ARCHITECTURE.md`
3. `TASKS.md`
4. Existing repo files only as needed

## Priorities
1. Preserve API behavior.
2. Change storage/infrastructure only.
3. Keep DB code in one small repository module.
4. Keep secrets out of Git.
5. One-command startup.
6. Lowest reasonable tokens/dependencies.

## Hard constraints
- Same repo, same Python/FastAPI lane.
- PostgreSQL via official Docker image.
- Use `psycopg[binary]` unless project already uses SQLModel.
- Read `DATABASE_URL` from environment; never hardcode credentials.
- `.env` git-ignored; `.env.example` committed.
- Named Docker volume for DB persistence.
- Same endpoint/request/response contracts.
- Preserve 200/201/204/400/404.
- Parameterized `%s` SQL only for request values.
- Routes contain no raw SQL.
- No optional extras before core acceptance passes.

## Change strategy
- Inspect A2 first.
- Reuse existing routes/validation/tests.
- Replace SQLite repository/storage with Postgres.
- Add only required infra: `Dockerfile`, `compose.yaml`, `.env.example`, `.dockerignore` if useful.
- Avoid unrelated refactors.

## Engineering rules
- KISS/YAGNI first; DRY only when useful.
- Preserve SOLID/GRASP/LoD without extra layers.
- No auth, Redis, Kubernetes, CI/CD, cloud, reverse proxy, migrations framework, or production hardening unless explicitly requested.
- No broad exception swallowing, dead code, TODO stubs, or secret logging.

## Verification
Verify:
- Postgres starts.
- App connects via `DATABASE_URL`.
- table auto-creates.
- exactly 3 seeds on first empty DB.
- CRUD uses Postgres.
- persistence survives `docker compose down` then `up`.
- `.env` is not tracked.
- `.env.example` is tracked.
- A1/A2 contract tests still pass.
- SQL is parameterized.
- API container uses DB host `db`, not `localhost`.

## Workflow
For each task: inspect minimal files -> implement smallest change -> run checkpoint -> fix -> tick `TASKS.md` -> commit stage.

## README
Include project purpose, `cp .env.example .env`, `docker compose up`, env vars, endpoint table, one `curl -i`, DB screenshot/psql proof, persistence note.

## Token discipline
Do not restate specs. Read targeted files only. Patch instead of rewrite. Keep logs concise. Stop when acceptance passes.

## Done
A clean clone can copy `.env.example`, run `docker compose up`, use unchanged CRUD against Postgres, restart the stack without data loss, and see the same rows directly in Postgres.
