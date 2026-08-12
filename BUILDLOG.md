# Build Log

## A3 Stage 0

- Used a temporary standalone PostgreSQL container for the database-only checkpoints in Stages 0–3; the required two-service Compose definition remains isolated to Stage 4.

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
