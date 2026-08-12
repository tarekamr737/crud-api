# Evidence

## Stage 0 — SQLite initialization

- `python -m pytest tests/test_db.py -q` → `2 passed in 0.06s`.
- The focused tests create a fresh temporary database, inspect the `tasks` table and exact seed rows, then initialize the same database three times and assert the row count remains exactly 3.
- `python -m pytest tests/test_api.py -q` → `9 passed in 0.66s`, proving the A1 contract still passes after startup initialization was added.
