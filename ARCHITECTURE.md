# ARCHITECTURE.md

## Stack
- Python 3.10+
- FastAPI
- Uvicorn
- Pydantic
- pytest + FastAPI TestClient for concise verification

FastAPI is chosen because Swagger UI/OpenAPI is generated automatically at `/docs`.

## Minimal structure
```text
.
├── AGENTS.md
├── PRODUCT.md
├── ARCHITECTURE.md
├── TASKS.md
├── README.md
├── requirements.txt
├── app/
│   └── main.py
└── tests/
    └── test_api.py
```

Keep API implementation in one file unless it becomes genuinely hard to read.

## Runtime design
`app/main.py` owns:
1. FastAPI app
2. Pydantic request models
3. 3 seeded task objects
4. helper to locate a task / generate next ID
5. route handlers

Data lives in a process-local Python list. Restarting the server resets it.

## Request contracts
POST body:
```json
{"title":"Buy milk"}
```

PUT body:
```json
{"title":"Buy oat milk","done":true}
```
At least one valid updatable field must be supplied.

### Important FastAPI detail
FastAPI normally emits `422` for schema validation failures, but this assignment requires `400`.
Implement request validation so required invalid POST/PUT bodies return `400` JSON errors. Keep the solution small; a targeted validation approach is preferred over a large global framework layer.

## IDs
Use the next free integer ID, e.g. `max(existing ids, default=0) + 1`.
Do not reuse deleted IDs unless that naturally becomes the next free value under the chosen rule.

## HTTP behavior
- GET success: `200`
- POST success: `201`
- PUT success: `200`
- DELETE success: `204`, empty body
- invalid request: `400`
- missing ID: `404`

Use consistent JSON errors:
```json
{"error":"..."}
```

## Swagger/OpenAPI
Use FastAPI route metadata (`summary`/`description`) so `/docs` is useful without maintaining a separate spec file.

## Testing strategy
Keep tests contract-focused:
- root + health
- list + get
- missing get → 404
- create → 201 + state visible
- invalid create → 400
- update title/done → 200
- invalid update → 400
- missing update/delete → 404
- delete → 204 + resource gone
- `/openapi.json` contains required paths

Tests should reset in-memory state between cases or avoid order-dependent assumptions.

## Commands
Install:
```bash
python -m pip install -r requirements.txt
```

Run:
```bash
uvicorn app.main:app --reload
```

Test:
```bash
pytest -q
```

Docs:
`http://localhost:8000/docs`

## Design principles
- KISS/YAGNI: no layers without need.
- DRY: tiny helpers only for repeated lookup/error logic.
- SOLID/GRASP/LoD: preserve clear responsibilities without ceremony.
- Security: validate untrusted input; no secrets; no arbitrary execution.
