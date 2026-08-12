# Build Log

## Stage 0

- Kept API routes list-backed for this stage so the database initialization change remains separate from the read/write migrations scheduled in Stages 1–3.
- Located `tasks.db` from the application package path so startup behavior does not depend on the shell's current directory.
