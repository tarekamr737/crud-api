# AGENTS.md

## Mission
Upgrade the existing A1 FastAPI CRUD API from in-memory storage to SQLite
without changing the public API contract.

## Read order
1. `PRODUCT.md`
2. `ARCHITECTURE.md`
3. `TASKS.md`
4. Existing code/tests/README only as needed

## Priorities
1. Preserve A1 behavior exactly.
2. Replace only storage concerns.
3. Use safe parameterized SQL.
4. Prove persistence.
5. Keep code/dependencies minimal.

## Hard constraints
- Continue in the SAME repo and SAME Python/FastAPI lane.
- Use SQLite database file `tasks.db`.
- Prefer Python stdlib `sqlite3`; do not add ORM unless already present.
- No in-memory task list as source of truth.
- Auto-create DB/table on startup.
- Table: `tasks(id INTEGER PRIMARY KEY, title TEXT, done INTEGER/BOOLEAN)`.
- Seed exactly 3 examples only when table is empty.
- Existing endpoints/request/response shapes stay unchanged.
- Preserve status codes: 200, 201, 204, 400, 404.
- Errors remain JSON.
- All user-supplied SQL values use `?` placeholders.
- Never concatenate/interpolate user input into SQL.
- `tasks.db` should normally be git-ignored.
- Do not build optional extras until required tasks pass.

## Change strategy
- Inspect existing A1 implementation before editing.
- Reuse route validation and schemas where correct.
- Replace storage calls behind routes; avoid route rewrites.
- Prefer 2–4 tiny DB helpers over a repository/service architecture.
- One connection per operation or one simple well-managed connection;
  choose the smallest reliable design for the existing app.
- Commit writes explicitly.
- Convert SQLite `done` 0/1 back to API boolean.

## Engineering rules
- KISS/YAGNI first.
- DRY only for repeated DB lookup/row conversion/connection logic.
- Preserve SOLID/GRASP/LoD without creating unnecessary layers.
- No new frontend, auth, Docker, cloud, migrations framework, cache, queue, ORM.
- No silent API contract changes.
- No broad exception swallowing.
- No dead code or TODO placeholders.

## Workflow
For each task:
1. Inspect only relevant existing files.
2. Implement smallest complete change.
3. Run narrow test/check.
4. Fix before continuing.
5. Mark `TASKS.md`.
6. Commit with the specified stage message.

## Verification
Always verify:
- DB/table auto-create
- seeding is idempotent
- CRUD reads/writes SQLite
- persistence after restart
- invalid bodies still 400
- unknown IDs still 404
- DELETE returns 204 empty
- old A1 endpoint tests still pass
- no SQL contains interpolated user input

## README update
Add:
- why SQLite
- `tasks.db` location + auto-creation
- clean-clone run command
- persistence explanation
- DB Browser screenshot reference
- one Stage 4 SQL query + result/observation

## Token discipline
- Do not restate specs.
- Read targeted files only.
- Patch instead of rewriting whole files.
- Keep logs/output concise.
- Stop when acceptance criteria pass.

## Definition of done
Same API, SQLite-backed storage, persistence proven, clean clone works,
README updated, DB screenshot captured, and honest stage commits exist.
