# Build Log

## A4 Baseline

- The repository `.venv` did not contain pytest, while system Python had pytest 8.4.2. A system-Python baseline run then stalled because PostgreSQL was unreachable and Docker API access was denied in the sandbox; it was terminated without modifying project state. Source inspection established the CRUD contract for later regression checks.

## A4 Stage 0

- Disabled Supabase client session persistence and automatic refresh because the singleton is server infrastructure shared across requests; authentication will use each request's explicit Bearer token instead of mutable client session state.

## A4 Stage 1

- FastAPI rejected the initial success-dictionary/`JSONResponse` union as an inferred response model. Set `response_model=None` on auth routes so each route can intentionally return either its success payload or normalized JSON error without changing runtime behavior.

## A4 Stage 3

- Supabase's ordinary `sign_out()` relies on mutable client session state, which is unsuitable for a shared server singleton. Logout therefore uses the SDK's token-explicit logout call with the already verified user JWT; the client remains configured with the anon/publishable key, never `service_role`.

## A4 Stage 4

- The first full regression run reached PostgreSQL during its one-time container initialization and exhausted the application's startup retries just before the server became ready. After the existing container reported `database system is ready to accept connections`, the unchanged suite passed in full.

## A4 Stage 5

- The in-app browser runtime reported no available browser while the locally running `/docs` endpoint returned HTTP 200. Kept the existing screenshot unchanged instead of fabricating a current auth-enabled capture; the README screenshot checklist remains open until a real browser capture is possible.
- The first cleanup filter matched the PowerShell command text that contained the Uvicorn arguments and interrupted its own shell after stopping the API. A narrower retry removed the exact disposable `a4-regression-postgres` container and verified workspace `.tmp` directory; no project data was removed.

## A3 Stage 0

- Used a temporary standalone PostgreSQL container for the database-only checkpoints in Stages 0–3; the required two-service Compose definition remains isolated to Stage 4.

## A3 Stage 4

- Used a ten-attempt, one-second `psycopg.OperationalError` retry for startup ordering because `depends_on` does not imply readiness and the optional database healthcheck is explicitly deferred.

## A3 Stage 5

- Native PowerShell and Command Prompt capture attempts could not obtain a window handle in this environment, and the in-app browser was unavailable. Rendered the already verified `psql` command/output locally with headless Chrome, then visually inspected the resulting PNG before committing it.

## Stage 0

- Kept API routes list-backed for this stage so the database initialization change remains separate from the read/write migrations scheduled in Stages 1–3.
- Located `tasks.db` from the application package path so startup behavior does not depend on the shell's current directory.

## Stage 1

- The first focused test collection failed because Pydantic on Python 3.11 rejects `typing.TypedDict`; switched the moved `Task` type to `typing_extensions.TypedDict`, matching the A1 implementation.

## Stage 4

- DB Browser's Windows CLI exited successfully but did not apply the SQL file, including after process synchronization and explicit transaction attempts. Switched to its visible Execute SQL workflow and retained the exact required statements in `docs/stage4.sql`.
- An initial global-keystroke GUI attempt targeted Chrome instead of DB Browser and opened a reload confirmation; canceled it without confirming or submitting anything. Replaced global input with DB Browser's `--sql` launch plus window-handle-specific capture.

## Stage 5

- The first clean-bootstrap proof command had a nested PowerShell/Python quoting error before application import. Split import and inspection into separate commands; the retry created the database and returned the exact seed rows/schema.
