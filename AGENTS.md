# AGENTS.md

## Mission
Build the assignment exactly as specified in `PRODUCT.md` and `ARCHITECTURE.md`.
Use `TASKS.md` as the execution order and source of progress.

## Priority
1. Correct assignment behavior.
2. Small, readable implementation.
3. Fast verification after every change.
4. Minimal dependencies/tokens.
5. No speculative features.

## Hard constraints
- Python 3.10+ + FastAPI.
- In-memory task list only. No DB, files, ORM, auth, Docker, frontend, or cloud.
- Keep production code intentionally small; prefer one `app/main.py`.
- Swagger UI must work at `/docs`.
- API errors must be JSON.
- Required invalid POST/PUT bodies must return **400**, not FastAPI's default 422.
- Unknown task IDs return **404**.
- DELETE success returns **204** with no body.
- Preserve the required endpoints and response semantics.
- Do not build optional/stretch features until core acceptance checks pass.
- Avoid abstractions used only once.

## Engineering rules
- KISS/YAGNI first; DRY only when duplication is meaningful.
- Prefer explicit code over patterns/framework layers.
- Use type hints and Pydantic where useful, but do not let framework defaults violate required status codes.
- Keep state access and ID generation deterministic and easy to understand.
- Never silently change API contracts.
- No broad exception swallowing.
- No dead code, TODO stubs, or placeholder implementations.
- No secrets or local environment files in Git.

## Workflow
For each task:
1. Read only the relevant section of `PRODUCT.md` / `ARCHITECTURE.md`.
2. Implement the smallest complete change.
3. Run the narrowest relevant verification.
4. Fix failures before continuing.
5. Mark the checkbox in `TASKS.md`.
6. Make the specified stage commit.

## Verification
Use FastAPI's test client or curl for behavior; always verify:
- status code
- JSON body when applicable
- state mutation
- 204 has no body
- `/docs` exposes all endpoints

Before completion run the complete CRUD flow:
create → list → get → update → delete → confirm missing.

## Git
Create meaningful commits matching assignment stages:
- Stage 0: hello server
- Stage 1: root and health endpoints
- Stage 2: read endpoints with 404
- Stage 3: create with validation
- Stage 4: full CRUD
- Stage 5: Swagger UI
- Stage 6: publish and docs
Optional extras get a separate commit.

Do not rewrite history just to make commit count look correct.

## README
Must include:
- what the project is
- exact install/run command(s)
- endpoint table
- one real `curl -i` output
- Swagger UI screenshot reference
- note that data is in memory and resets on restart

## Token discipline
- Do not restate specs in chat/logs.
- Do not explain routine edits unless blocked.
- Prefer patching existing files over generating large replacements.
- Read targeted files/sections only.
- Keep command output concise.
- Stop when acceptance criteria pass.

## Definition of done
All required checks in `TASKS.md` pass, README is usable by a stranger,
Git history has honest stage commits, and no out-of-scope infrastructure exists.
