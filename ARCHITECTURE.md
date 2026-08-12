# ARCHITECTURE.md

## Stack
Keep the existing stack:
- Python 3.10+
- FastAPI
- Uvicorn
- Pydantic
- pytest / FastAPI TestClient

Add no database dependency:
- use Python standard-library `sqlite3`

## Target structure
Keep the existing repo structure. Prefer minimal change, for example:

```text
.
├── app/
│   ├── main.py
│   └── db.py          # optional; only if it reduces repeated DB code
├── tests/
│   └── test_api.py
├── tasks.db           # runtime-created, git-ignored
├── .gitignore
├── README.md
├── AGENTS.md
├── PRODUCT.md
├── ARCHITECTURE.md
└── TASKS.md
```

Do not reorganize a working A1 project just to match this example.

## Storage design

### Connection
Use:
```python
sqlite3.connect(DB_PATH)
```

Configure row access if useful:
```python
conn.row_factory = sqlite3.Row
```

Keep connection lifetime obvious and safe. A small helper/context-manager is enough.

### Initialization
On application startup or module initialization:
```sql
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0
);
```

Then:
```sql
SELECT COUNT(*) FROM tasks;
```

If count is zero, insert the 3 A1 seed tasks.

Prefer one transaction for the seed if simple.

## Row mapping
SQLite stores `done` as 0/1. API returns boolean.

Conceptually:
```python
{
    "id": row["id"],
    "title": row["title"],
    "done": bool(row["done"]),
}
```

## Route storage mapping

### GET `/tasks`
```sql
SELECT id, title, done FROM tasks;
```

### GET `/tasks/{id}`
```sql
SELECT id, title, done FROM tasks WHERE id = ?;
```

### POST `/tasks`
```sql
INSERT INTO tasks (title, done) VALUES (?, ?);
```

Use `cursor.lastrowid`, then return the inserted task.

### PUT `/tasks/{id}`
Preserve current A1 partial-update semantics.

Recommended small approach:
1. fetch current row
2. 404 if missing
3. merge supplied fields with existing values
4. execute:
```sql
UPDATE tasks
SET title = ?, done = ?
WHERE id = ?;
```
5. return updated row

### DELETE `/tasks/{id}`
```sql
DELETE FROM tasks WHERE id = ?;
```

Check existence/affected rows; missing -> 404.
Success -> 204 empty body.

## SQL safety
Correct:
```python
conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
```

Forbidden:
```python
f"SELECT * FROM tasks WHERE id = {task_id}"
```

All request-derived values must be bound parameters.

## Testing strategy

### Preserve A1 contract tests
Old endpoint tests are regression tests and should keep passing.

### Add DB-focused tests
Test:
- DB created when missing
- table created when missing
- seed exactly once
- restart/reinitialize does not duplicate seeds
- create persists across a fresh app/connection
- update persists
- delete persists
- API and direct DB rows agree

Use an isolated temporary SQLite file for automated tests if practical.
Never let tests depend on the developer's real `tasks.db`.

## Manual verification
1. delete local `tasks.db`
2. start app
3. verify exactly 3 tasks
4. create another task
5. stop app
6. restart
7. verify new task remains
8. open DB Browser and confirm same rows
9. change data in DB Browser
10. call API and confirm change is immediately visible

## Git hygiene
Add:
```gitignore
tasks.db
*.db-journal
```

Do not commit local DB state unless the assignment specifically requires it.

## Design principles
The API is the stable contract; SQLite is an implementation detail.
Change storage, not behavior.
