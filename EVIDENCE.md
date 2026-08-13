# Evidence

## Week 7 Stage 5 — Eval, README, and release readiness

- `.venv\Scripts\python.exe evals\run_evals.py` made real calls with production retries only and returned `score=100.0`, `passed_checks=24`, `total_checks=24`, `failed_case_ids=[]`, date `2026-08-13`, and prompt `triage-v1`.
- All eight labelled cases passed: normal billing, clear bug, feature request, generic other, urgent outage, ambiguous, prompt injection, and empty-ish valid input.
- A successful eval call logged 550 input tokens, 38 output tokens, 2,327 ms, and repair count 0; README records that exact structured line and estimates 5.88 million tokens and $0 provider charge at 10,000 daily requests on the selected free route.
- The README's required sections were present in the mandated order and include a runnable real-model curl with an exact observed response, job card, provider/model settings, real eval result, cost log, daily estimate, and one honest next improvement.
- The Stage 5 regression returned `46 passed in 1.89s`; `compileall` passed for `src`, `app`, and `evals`, the eval fixture count was exactly 8, and `git diff --check` passed.
- `.env` is ignored and untracked, its history query returned no commits, and the tracked-source scan found no OpenRouter `sk-or-v1-` token.
- The Docker image now copies `src`, `prompts`, and `logs` alongside `app`, making the triage route and versioned prompt available in the existing Compose runtime.
- Pushed `agent/llm-support-triage` to the public canonical repository and opened draft PR [#1](https://github.com/tarekamr737/Back-End-AI-Engineering-FlyRank-Intern/pull/1) against `main`.

## Week 7 Final audit — HTTP contract

- `.venv\Scripts\python.exe -m pytest tests\test_triage_final_audit.py tests\test_triage.py tests\test_llm_retry.py tests\test_llm_client.py tests\test_triage_schema.py tests\test_triage_prompt.py tests\test_evals.py tests\test_auth.py tests\test_auth_dependency.py -q --basetemp=.tmp\pytest-w7-final` returned `47 passed in 2.06s`.
- The dedicated final matrix exercised HTTP 200, 400, 422, 503, and 504 in one test. It proved invalid input and the kill switch make zero completion calls, 422 makes exactly one repair call, and neither raw model text nor private timeout detail reaches HTTP output.

## Week 7 Final audit — Fresh snapshot and invariants

- Exported committed `f70e820` into a new ignored directory on D:, copied `.env.example` to `.env`, created a fresh D:-local `.venv`, installed the committed requirements, and reran the committed final suite with `47 passed in 3.46s`.
- Fresh environment creation, dependency installation, and tests took approximately 122 seconds total, below the five-minute requirement. The venv, pip cache, temp directory, and pytest base temp all remained under the D: snapshot.
- `LLM_TIMEOUT_SECONDS` is `30.0`, SDK retries are disabled, and the custom policy is capped at three attempts. Tests prove output failure triggers no more than one repair call and raw model strings never enter HTTP responses.
- `git rev-list --count origin/main..HEAD` returned 7 meaningful feature/audit commits, including each required Stage 0 through Stage 5 message.
- `.env` is untracked and absent from history. Current-tree and all-history scans using a key-shaped OpenRouter regex returned no credential value; the literal prefix occurrence is only the documented audit statement itself.
- Draft PR [#1](https://github.com/tarekamr737/Back-End-AI-Engineering-FlyRank-Intern/pull/1) is open from `agent/llm-support-triage` to `main`.

## Week 7 Stage 4 — Timeout, retries, logging, and kill switch

- `.venv\Scripts\python.exe -m pytest tests\test_llm_client.py tests\test_llm_retry.py tests\test_triage.py tests\test_triage_schema.py tests\test_triage_prompt.py -q --basetemp=.tmp\pytest-w7-stage4` returned `27 passed in 1.85s`.
- Client configuration tests prove `timeout == 30.0` and SDK `max_retries == 0`; custom tests prove 1s/2s exponential delays, jitter, numeric `Retry-After`, and three attempts total for timeout/429/5xx.
- Parameterized 400, 401, and 403 tests each made exactly one provider attempt with no sleep. A live request using a deliberately wrong process-only key emitted exactly one structured call log and returned `status=401`, proving no hidden retry.
- Every mocked provider attempt emitted one parseable JSON line containing exactly prompt version, model, input tokens, output tokens, duration milliseconds, and repair count; successful usage recorded `11` input and `7` output tokens.
- `LLM_ENABLED=false` took precedence over `LLM_STUB=1`, returned safe HTTP 503, and left the completion mock uncalled. Exhausted timeout mapped to safe 504; other provider failure mapped to safe 503.
- The final Stage 4 triage/client/auth regression returned `44 passed in 1.89s`; `compileall` and `git diff --check` also passed.

## Week 7 Stage 3 — Parse, repair once, and quarantine

- `.venv\Scripts\python.exe -m pytest tests\test_triage.py tests\test_triage_schema.py tests\test_triage_prompt.py tests\test_llm_client.py -q --basetemp=.tmp\pytest-w7-stage3` returned `18 passed in 1.53s`.
- A forced `category="sales"` schema violation caused exactly two completion calls total; the second request contained the broken output and safe validation error, and its valid repair returned HTTP 200.
- Two forced non-JSON completions caused exactly one repair attempt, then HTTP 422 with only `Model output did not match the required schema`; neither raw string appeared in the response.
- The second-failure test appended exactly one JSONL record containing timestamp, sanitized single-line input, final raw output, safe parse error, and `triage-v1` to an isolated quarantine path.
- `.gitignore` excludes `logs/*.jsonl`, while `logs/.gitkeep` preserves the intended runtime directory without committing quarantined content.
- The final Stage 3 triage/client/auth regression returned `35 passed in 1.44s`; `compileall`, `git diff --check`, and an explicit quarantine ignore check also passed.

## Week 7 Stage 2 — Versioned prompt and real-model wiring

- `.venv\Scripts\python.exe -m pytest tests\test_triage.py tests\test_triage_prompt.py tests\test_triage_schema.py tests\test_llm_client.py -q --basetemp=.tmp\pytest-w7-stage2` returned `16 passed in 1.45s`.
- Prompt tests prove `prompts/triage-v1.md` contains role, exact schema/enums, hard rules, unsure behavior, and three examples in the required order, including ambiguous and hostile inputs.
- A hostile multiline input remained absent from the system prompt and appeared only as escaped JSON in the separate user message; the client test proves temperature is exactly 0.
- Three synthetic real-model checks returned schema-valid results: duplicate charge -> `billing/normal/billing`; reproducible app crash -> `bug/high/engineering`; vague issue -> `other/low/support` with confidence `0.3`.
- The free upstream pool returned transient null choices and 429 responses during the checkpoint; bounded retries, including the advertised 24-second interval, succeeded without changing the selected model.
- The final Stage 2 regression across triage, prompt, schema, client, and existing auth tests returned `33 passed in 1.47s`; `compileall` also completed successfully for `src` and `app`.

## Week 7 Stage 1 — Schema, endpoint, and stub mode

- `.venv\Scripts\python.exe -m pytest tests\test_triage.py tests\test_triage_schema.py tests\test_llm_client.py -q --basetemp=.tmp\pytest-w7-stage1` returned `12 passed in 1.48s`.
- The endpoint test made two different valid requests with `LLM_STUB=1`, received the same schema-valid HTTP 200 JSON, and proved the OpenAI completion method was never called.
- Missing, empty, oversized, extra-field, and null bodies returned HTTP 400 naming the offending field while the provider method remained uncalled.
- `.venv\Scripts\python.exe -m pytest tests\test_auth.py tests\test_auth_dependency.py -q --basetemp=.tmp\pytest-w7-stage1-auth` returned `17 passed in 0.89s`, preserving the existing auth validation behavior.
- `README.md` contains runnable PowerShell startup plus valid and invalid `curl.exe` examples for `/triage`.

## Week 7 Stage 0 — Provider readiness

- `.venv\Scripts\python.exe -m pytest tests\test_llm_client.py -q --basetemp=.tmp\pytest-w7-stage0` returned `3 passed in 0.71s`.
- A bounded live OpenRouter completion using `google/gemma-4-26b-a4b-it:free` returned exactly `ready`; the key was loaded only from the ignored `.env` and was never printed.
- `git check-ignore -v .env` matched `.gitignore:6:.env`; `.env` remains absent from tracked files, while `.env.example` contains all five LLM variable names with no secret.
- All SDK files and test artifacts remain inside the repository-local `.venv` and `.tmp` directories on `D:`.

## W5 A9 — Public repository delivery

- With explicit authorization to publish the repository's pre-existing API
  code together with the scraper, `git push origin main` advanced public
  `https://github.com/tarekamr737/crud-api.git` from `2bdd61c` to `d85abc1`.
- `git ls-remote origin refs/heads/main` returned
  `d85abc1f7de257b552c051892f937d95578e8c70`, exactly matching local `HEAD`
  before this delivery bookkeeping commit.
- The pushed history contains 20 verified scraper implementation/acceptance
  commits plus the professional README and global-skill cleanup commit.

## W5 A9 — Professional README and global skills

- Replaced the outdated root API-only README with a professional scraper
  overview covering verified results, architecture, setup, outputs, schema,
  politeness, resilience, testing, structure, ethics, limitations, and the
  earlier API work retained in the repository.
- Installed current upstream `supabase` 0.1.2 and
  `supabase-postgres-best-practices` 1.1.1 into
  `C:\Users\tarek\.codex\skills`; `quick_validate.py` returned `Skill is
  valid!` for both global folders.
- Removed the two now-redundant repository-scoped skill bundles and
  `skills-lock.json` only after the global validations passed.
- The post-change scraper regression returned `32 passed in 0.48s`;
  `git diff --check` passed, no real `.env` file is tracked, and the tracked
  source secret-pattern audit returned zero matching files.

## W5 A9 — Final core acceptance

- `..\.venv\Scripts\python.exe -m pytest -q --basetemp=.tmp\pytest`
  returned `32 passed in 0.36s`.
- Direct final output inspection returned `books=60 unique=60 errors=0
  catalogue=3 discovered=60 valid=60 failed=0`.
- The successful rerun report records `pages_fetched=0` and `cache_hits=63`;
  the fake-URL acceptance separately proves one broken detail page does not
  prevent 60 good records.
- `git rev-list --count 2bdd61c..HEAD` returned 19 meaningful W5 A9 commits
  before this final acceptance commit, exceeding the required seven.

## W5 A9 — Clean-snapshot run command

- Exported committed `HEAD` to a fresh ignored directory under
  `scraper/.tmp/` on `D:`, linked the already installed `D:` virtual
  environment, and copied the verified cache so validation would not repeat
  target requests.
- From that fresh snapshot, the README's exact
  `.\.venv\Scripts\python.exe -m src.main` command exited 0 and printed
  `catalogue_pages=3 discovered=60 unique_urls=60 valid_records=60
  invalid_records=0 failed_pages=0`.
- Direct snapshot output checks returned `books=60 cache_hits=63
  pages_fetched=0`, proving the committed project runs from its documented
  entry point without relying on uncommitted source files.

## W5 A9 — Git/cache hygiene

- `git check-ignore` matched all three generated JSON outputs and the cache;
  `git ls-files -- scraper/cache` returned no tracked cache files.
- `git status --short -- scraper` showed only the intentional `.gitignore` and
  README edits plus `output/sample-run-report.json`; the 115 KB live
  `books.json`, empty `errors.json`, live report, and 63 HTML pages remain local
  and ignored on `D:`.
- The committed representative report parses as JSON and records 60 valid
  records and 63 cache hits.

## W5 A9 — Complete README

- A content checklist found every required section in `scraper/README.md` and
  `git diff --check` returned no formatting errors.
- The README now takes a stranger from Python 3.10+ installation to the single
  run command, names all three outputs, defines the record schema, documents
  caching/politeness/retries, includes the verified 60-record cached report,
  states one selector-coupling limitation, explains why no browser is needed,
  and includes the required ethics/site-reuse language.

## W5 A9 — Live 60-book run and rerun

- The first successful cached live run printed `catalogue_pages=3
  discovered=60 unique_urls=60 valid_records=60 invalid_records=0
  failed_pages=0`.
- An immediate second successful CLI run printed the same counts. Direct JSON
  checks returned `books=60 unique=60 errors=0 pages_fetched=0 cache_hits=63
  valid=60 failed=0`, proving every scoped page came from cache and no duplicate
  or invalid record entered output.
- `..\.venv\Scripts\python.exe -m pytest tests\test_fetcher.py -q
  --basetemp=.tmp\pytest` returned `9 passed`, including the regression test
  that successful target responses are decoded as UTF-8 before caching.

## W5 A9 — Broken URL acceptance

- `..\.venv\Scripts\python.exe -m pytest
  tests\test_pipeline.py::test_one_fake_url_still_finishes_with_sixty_good_records
  -q --basetemp=.tmp\pytest` returned `1 passed`.
- The test runs 60 unique valid detail jobs plus one fake URL that raises an
  HTTP 404 `FetchError`; processing and validation finish with 60 unique valid
  records, zero invalid records, and exactly one recorded page failure.

## W5 A9 — Run report

- `..\.venv\Scripts\python.exe -m pytest tests\test_pipeline.py -q
  --basetemp=.tmp\pytest` returned `9 passed`.
- A deterministic full-pipeline test fetches three catalogue plus three detail
  pages and reads `run-report.json` back from disk. It proves exact
  `start_time`, `duration=2.5`, `pages_fetched=6`, `cache_hits=0`, three
  catalogue/discovered/unique/valid counts, zero invalid/failed counts, and an
  empty failure list.
- `src.main` now invokes this orchestrator and prints the concise required run
  summary without containing HTML selectors.

## W5 A9 — Retry policy

- `..\.venv\Scripts\python.exe -m pytest tests\test_fetcher.py -q
  --basetemp=.tmp\pytest` returned `8 passed`.
- Sequence-based tests prove 5xx → 200 and timeout → 200 each make exactly two
  requests, two 5xx responses fail after exactly two requests, and 403/404
  each fail after exactly one request.
- Both transient attempts receive the 0.5-second delay; every attempt still
  uses the same identifiable User-Agent and explicit timeout.

## W5 A9 — Page-level fault isolation

- `..\.venv\Scripts\python.exe -m pytest tests\test_pipeline.py -q
  --basetemp=.tmp\pytest` returned `8 passed`.
- The fault-isolation test processes good → HTTP 404 → good detail URLs,
  verifies all three were attempted in order, receives both good normalized
  records, and receives one failure containing the broken URL and reason.
- The detail boundary catches only expected fetch, parse/normalization, and
  cache I/O failures; it logs the affected URL and continues safely.

## W5 A9 — Canonical idempotency

- `..\.venv\Scripts\python.exe -m pytest tests\test_pipeline.py -q
  --basetemp=.tmp\pytest` returned `7 passed`.
- The idempotency test submits two candidates with the same canonical
  `product_url`, proves first-seen deduplication returns one candidate, writes
  twice, and verifies byte-identical `books.json` output with exactly one row.
- Storage rebuilds both JSON files from the current run and never appends to an
  existing output.

## W5 A9 — Validation routing

- `..\.venv\Scripts\python.exe -m pytest tests\test_pipeline.py -q
  --basetemp=.tmp\pytest` returned `6 passed`.
- The storage-boundary test submits one valid and one empty-title candidate,
  then reads both generated JSON files back from disk: `books.json` contains
  only the valid record and `errors.json` contains the rejected record, its
  canonical URL, and Pydantic's reason.

## W5 A9 — Pydantic record schema

- `..\.venv\Scripts\python.exe -m pytest tests\test_models.py -q
  --basetemp=.tmp\pytest` returned `10 passed`.
- The finished `BookRecord` contains each of the eight raw/provenance fields
  plus numeric `price_gbp`, forbids extra fields, permits `description=None`,
  and serializes URLs and timestamps as JSON strings.
- Parameterized malformed-record tests reject an empty title, invalid product
  URL, negative price, and invalid timestamp.

## W5 A9 — Price normalization

- `..\.venv\Scripts\python.exe -m pytest tests\test_models.py -q
  --basetemp=.tmp\pytest` returned `5 passed`.
- Tests prove `£51.77` becomes the float `51.77`, normalization retains the
  original `price_text`, and empty, currency-less, or non-numeric inputs are
  rejected.

## W5 A9 — Raw book extraction

- `..\.venv\Scripts\python.exe -m pytest tests\test_parser.py -q
  --basetemp=.tmp\pytest` returned `3 passed`.
- Tests prove exact extraction of all eight raw fields, `None` for a missing
  description, and an explicit error for a missing required selector.
- A cached-catalogue/live-detail check printed `raw_fields=8
  title_present=True rating=Three description_present=True pages_fetched=1
  cache_hits=3`, validating the selectors against the target's real HTML while
  making only one new request.

## W5 A9 — Book URL discovery

- `..\.venv\Scripts\python.exe -m pytest tests\test_pipeline.py -q
  --basetemp=.tmp\pytest` returned `5 passed`, including relative URL
  resolution, stable duplicate removal, and a deterministic 60-book fixture.
- A live run against the designated sandbox printed three `FETCH` lines and
  `catalogue_pages=3 unique_urls=60 pages_fetched=3 cache_hits=0`; its assertion
  proved all 60 discovered absolute product URLs were unique.
- The three catalogue responses were cached only under the ignored
  `scraper/cache/` directory on `D:`.

## W5 A9 — Catalogue traversal

- `..\.venv\Scripts\python.exe -m pytest tests\test_pipeline.py -q
  --basetemp=.tmp\pytest` returned `2 passed`.
- The traversal test starts at the site root, follows two different relative
  `next` links, fetches pages 1–3 in order, and proves page 4 is not fetched.
- A missing `next` link before the three-page scope is complete produces an
  explicit error naming the expected limit.

## W5 A9 — HTML cache

- `..\.venv\Scripts\python.exe -m pytest tests\test_fetcher.py -q
  --basetemp=.tmp\pytest` returned `3 passed` with all test files under the
  `D:` workspace.
- The cache test calls the same URL twice, observes exactly one HTTP boundary
  call, one hashed `.html` file, counters of `pages_fetched=1` and
  `cache_hits=1`, and exact `FETCH` then `CACHE HIT` console messages.

## W5 A9 — Polite HTTP fetch

- `..\.venv\Scripts\python.exe -m pytest tests\test_fetcher.py -q` returned
  `2 passed`.
- The focused tests prove every request receives an identifiable User-Agent,
  the declared 15-second timeout, a 0.5-second delay, and that non-200 content
  raises `FetchError` instead of being returned for parsing.

## W5 A9 — Target classification

- A polite request with an identifiable User-Agent and 15-second timeout to
  `https://books.toscrape.com/robots.txt` returned HTTP 404 on 2026-08-13.
- The target homepage describes itself as a demo website for web-scraping
  purposes, and `scraper/README.md` limits collection to the first three
  catalogue pages and their 60 discovered products.
- The README records the target, robots result, collected fields, scope, and
  required site-reuse ethics statement.

## A4 Baseline — Existing CRUD inspection

- `app/main.py` exposes the existing `/`, `/health`, `/tasks`, and `/tasks/{task_id}` contracts and delegates all persistence to `app/repository.py`.
- `app/repository.py` remains the sole PostgreSQL layer and uses bound `%s` parameters for request-derived values.
- The existing suite contains 16 CRUD/database regression tests covering validation, status codes, persistence, and OpenAPI paths.
- `.env` is ignored by `.gitignore` and absent from `git ls-files`; `.env.example` is tracked.

## A4 Stage 0 — Supabase client setup

- Installed and imported `supabase` 2.31.0 from the repository-local `.venv` on `D:`; `requirements.txt` bounds the supported major version to `<3.0`.
- `.env.example` now includes placeholder `SUPABASE_URL` and `SUPABASE_KEY` values while preserving the runnable PostgreSQL settings.
- A focused configuration check created the client from only those two variables and returned `configured`; a clean process without them returned the stable startup error `Missing required environment variable: SUPABASE_URL`.
- `git check-ignore -v .env` matched `.gitignore`, `git ls-files .env.example` found the template, and `git ls-files --error-unmatch .env` confirmed the real file is untracked.

## A4 Stage 1 — Signup and login

- `.venv\Scripts\python.exe -m pytest tests\test_auth.py -q` returned `6 passed`.
- Signup tests prove HTTP 201 returns only `id`, `email`, and `created_at`; missing/blank fields and provider failures return stable JSON 400 responses without provider details.
- Login tests prove HTTP 200 returns access and refresh tokens; missing/blank fields return JSON 400 and rejected credentials return stable JSON 401 without provider details.
- The request model passes passwords directly to Supabase and no application code stores, hashes, signs, or logs credentials or tokens.

## A4 Stage 2 — Public and protected routes

- `.venv\Scripts\python.exe -m pytest tests\test_auth.py tests\test_auth_dependency.py -q` returned `13 passed`.
- `/public/info` returns the exact required message with HTTP 200 and no authentication header.
- The reusable `HTTPBearer` dependency rejects missing, non-Bearer, empty, whitespace-containing, invalid, and expired/tampered credentials with stable JSON 401 responses and a `WWW-Authenticate: Bearer` header.
- A valid token is passed unchanged to `supabase.auth.get_user(token)`; the verified user then reaches both `/protected/profile` and `/protected/dashboard` through the same dependency.
- Profile output is limited to `id`, `email`, and `created_at`; the dashboard exposes only a message and verified user ID.

## A4 Stage 3 — Logout and Swagger Bearer auth

- `.venv\Scripts\python.exe -m pytest tests\test_auth.py tests\test_auth_dependency.py -q` returned `17 passed`.
- Logout first verifies the user with `get_user(token)`, then passes the same explicit user JWT to Supabase logout and returns HTTP 204 with an empty body; a missing token returns 401 before logout is called.
- Token cases explicitly cover valid, missing, Basic/non-Bearer, empty Bearer, whitespace-malformed, expired, and tampered values.
- The generated OpenAPI schema defines `HTTPBearer` as an HTTP bearer scheme, attaches it to both protected reads and logout, and leaves public info, signup, and login unlocked.

## A4 Stage 4 — CRUD regression and secret audit

- Started the already-installed PostgreSQL 17 image with its temporary data directory bind-mounted under `D:\FlyRank Intern\Connecting CRUD to the database\.tmp\a4-pgdata`; no database files were placed on `C:`.
- `.venv\Scripts\python.exe -m pytest -q` against the ready PostgreSQL instance returned `33 passed`, covering all existing CRUD/database behavior plus the new authentication tests.
- Git audit returned `env_tracked=False` and `env_in_history=False`; `.gitignore` remains the matching ignore rule for `.env`.
- At the Stage 4 audit, the local `.env` contained no Supabase values; no local Supabase value was found in history, and `rg` found no `service_role` or hard-coded `SUPABASE_KEY` assignment in `app/` or `tests/`. Real publishable configuration was added later only to the ignored `.env`.

## A4 Stage 5 — Live Supabase and Swagger verification

- The authenticated, project-scoped Supabase MCP returned project URL `https://whkdqsjdnrdaesnptkhe.supabase.co`, matching the configured project reference.
- Supabase MCP Auth logs proved a live signup returned success and requested confirmation; the following login failed with provider code `email_not_confirmed`, identifying the remaining live-flow blocker without exposing user data or tokens.
- Chrome DevTools loaded `http://127.0.0.1:8000/docs`; its accessibility tree contained the global **Authorize** control and authentication controls on `/protected/profile`, `/protected/dashboard`, and `/auth/logout`, while public/signup/login routes remained unlocked.
- Captured and visually inspected the current `docs/swagger-ui.png`; it clearly shows the auth endpoints, public/protected routes, Authorize control, and protected-route lock icons.

## A4 Final — Live hosted Auth flow

- With Confirm Email disabled in the hosted project's Email provider settings, a disposable live signup returned HTTP 201 and its immediate password login returned HTTP 200 with both access and refresh token fields present; no credential or token value was printed or stored.
- The returned access token reached `/protected/profile` and `/protected/dashboard` with HTTP 200. The same profile request returned HTTP 401 when the token was omitted and when its signature was tampered with.
- `/public/info` remained accessible with HTTP 200 and authenticated `/auth/logout` returned HTTP 204.
- Authenticated, project-scoped Supabase MCP logs independently showed two successful hosted signups, two successful password token exchanges, repeated successful user verification, one provider-level rejection of the tampered token, and two successful logouts.
- Current Supabase MCP documentation confirms that disabling Confirm Email autoconfirms email/password signups and permits immediate password login; its changelog search found no breaking change affecting this behavior.
- `.venv\Scripts\python.exe -m pytest -q` against a disposable PostgreSQL 17 instance with its data under the `D:` workspace returned `33 passed in 7.09s`; the container and verified temporary data directory were then removed.

## A4 Push — Public repository delivery

- `git push origin main` advanced the public repository from `e6d9634` to A4 Stage 6 commit `ab24e3a`.
- `git ls-remote origin refs/heads/main` returned `ab24e3ad35b14933d27d644eb5219980cac9bcf5`, exactly matching local `HEAD` before this delivery bookkeeping commit.
- The A4 range contains meaningful Stage 0, 1, 2, 3, 4, 5, and 6 commits, plus the separately committed Supabase agent skills installation.

## A3 Stage 0 — PostgreSQL in Docker

- `docker volume create crud-api-taskdata` created the named persistence volume.
- `docker run ... postgres:17-alpine` started the official PostgreSQL image as `crud-api-postgres`, mounting `crud-api-taskdata` at `/var/lib/postgresql/data`.
- `docker exec crud-api-postgres psql -U tasks_user -d tasks -c "SELECT current_database(), current_user;"` returned database `tasks` and user `tasks_user`.
- `git check-ignore .env` confirms local credentials are excluded from Git.

## A3 Stage 1 — Environment connection, schema, and seeds

- Installed `psycopg[binary]` 3.3.4 and added its bounded requirement.
- Ran three separate `python -c "import app.main"` startups with `DATABASE_URL=postgresql://tasks_user:tasks_password@localhost:5432/tasks`; all exited 0.
- Direct `psql` inspection after the third startup showed the required `SERIAL`/`TEXT`/`BOOLEAN` schema and exactly 3 rows: `Buy milk` false, `Write report` true, and `Call dentist` false.
- `python -m pytest -q` with the PostgreSQL URL set returned `15 passed in 0.78s`, preserving the existing contract during this staged initialization change.
- `.env` contains the local host URL and is ignored; committed `.env.example` contains the Compose service host `db`.

## A3 Stage 2 — PostgreSQL reads

- `python -m pytest tests/test_api.py::test_read_tasks_and_missing_task -q` with the PostgreSQL URL set returned `1 passed in 0.62s`.
- The unchanged endpoint assertions received the three PostgreSQL seed rows with HTTP 200, received task 2 by ID with HTTP 200, and retained the JSON HTTP 404 response for ID 99.
- `app/repository.py` binds the route ID with `WHERE id = %s` and `(task_id,)`; routes contain no SQL.

## A3 Stage 3 — Full PostgreSQL CRUD

- `python -m pytest -q` with the PostgreSQL URL set returned `16 passed in 2.68s`.
- The preserved API tests prove POST 201, PUT 200, DELETE 204 with an empty body, invalid POST/PUT 400 JSON, and missing-resource 404 JSON behavior.
- Repository tests create ID 4, update task 1, delete task 2, call database initialization again, and confirm all mutations remain in PostgreSQL.
- The API/database integration test verifies created, updated, and deleted state through a separate PostgreSQL connection after each HTTP mutation.
- A source audit found no SQLite import or route SQL. Every request-derived title, boolean, and ID is passed separately to a `%s` placeholder in `app/repository.py`.

## A3 Stage 4 — Full Compose stack

- `docker compose config` resolved exactly two services, `api` and `db`, and the API URL to `postgresql://tasks_user:tasks_password@db:5432/tasks`.
- `docker compose up --build -d` built the minimal Python image, started both containers, and created the named `connectingcrudtothedatabase_taskdata` volume.
- `docker compose ps` reported both services `Up`; direct inspection inside the API container confirmed its database host is `db`.
- `GET http://127.0.0.1:8000/tasks` returned HTTP 200 and the three seed tasks; `psql` in the Compose DB container independently returned `task_count = 3`.
- `python -m pytest -q` returned `16 passed in 3.17s` after the bounded startup retry and container files were added.

## A3 Stage 5 — Documentation and clean clone

- README now documents the FastAPI/PostgreSQL stack, `cp .env.example .env`, `docker compose up`, all four environment variables, every endpoint, a `curl -i` POST, direct `psql` inspection, and named-volume persistence.
- Captured and visually inspected `docs/postgres-psql.png`; it clearly shows the verified direct query and all three seed rows.
- Exported the staged Git tree into a new directory with no `.env`, copied `.env.example` to `.env`, and ran the documented `docker compose up --build -d` flow successfully.
- The clean snapshot reported both services `Up`, `GET /tasks` returned HTTP 200 with exactly three seeds, and direct `psql` returned the identical rows.
- Removed only the disposable clean-clone containers, network, volume, and verified temporary directory after the check passed.

## A3 Test — Contract, SQL safety, and secrets

- `python -m pytest -q` against PostgreSQL returned `16 passed in 2.66s`, covering all A1/A2 endpoint behavior plus schema, idempotent seed, persistence, and direct database agreement.
- Enumerated every `execute`/`executemany` call in `app/repository.py`; an AST check returned `interpolated_sql_calls=[]`, proving no SQL argument is an f-string or concatenated expression.
- `rg` found no SQL statement in `app/main.py`, so routes remain storage-agnostic.
- `git check-ignore -v .env` matched `.gitignore`; `git ls-files --error-unmatch .env` confirmed it is absent from Git, while `git ls-files .env.example` confirmed the template is tracked.

## A3 Final — Full-stack restart persistence

- Started the main Compose project on its preserved `taskdata` volume and created `Restart survivor one` (ID 4) and `Restart survivor two` (ID 5) through POST `/tasks`.
- Ran `docker compose down` followed by `docker compose up -d`, recreating both containers and their network without deleting the named volume.
- After restart, GET `/tasks` returned HTTP 200 with all five rows, including both new tasks under their original IDs.
- Direct `psql` returned the same five IDs, titles, and boolean values in order; `docker compose ps` reported both recreated services `Up`.

## A3 Push — Public repository delivery

- `git push origin main` updated `https://github.com/tarekamr737/crud-api.git` from `cdf8737` to `ed9a4ca`.
- `git ls-remote origin refs/heads/main` returned `ed9a4cadbeb8b85503c5380723f809b7099dd12f`, exactly matching the local FINAL commit before this delivery bookkeeping commit.
- Audited the linear history and confirmed the required Stage 0 through Stage 5 messages, followed by dedicated TEST and FINAL commits; each stage was committed only after its recorded checkpoint passed.

## Stage 0 — SQLite initialization

- `python -m pytest tests/test_db.py -q` → `2 passed in 0.06s`.
- The focused tests create a fresh temporary database, inspect the `tasks` table and exact seed rows, then initialize the same database three times and assert the row count remains exactly 3.
- `python -m pytest tests/test_api.py -q` → `9 passed in 0.66s`, proving the A1 contract still passes after startup initialization was added.

## Stage 1 — Database read endpoints

- `python -m pytest tests/test_db.py tests/test_api.py::test_read_tasks_and_missing_task -q` → `4 passed in 0.57s`.
- The database read test changes a row through a separate SQLite connection and verifies `fetch_tasks`/`fetch_task` immediately return that state with integer `done` values converted to booleans.
- GET by ID uses `WHERE id = ?` with the route ID passed as a bound parameter; the existing endpoint test proves the 200 and JSON 404 responses are unchanged.

## Stage 2 — Database inserts

- `python -m pytest tests/test_db.py tests/test_api.py::test_create_rejects_invalid_bodies tests/test_api.py::test_create_assigns_next_id_and_updates_state -q` → `9 passed in 0.55s`.
- The focused persistence test inserts `Ship API`, reinitializes the database to simulate a restart, then reads ID 4 from a fresh connection and gets the same task.
- POST continues to return 201, invalid bodies return the unchanged JSON 400, and both the title and generated ID are handled through parameterized SQL/SQLite `lastrowid`.

## Stage 3 — Database updates and deletes

- `python -m pytest -q` → `14 passed in 0.66s`.
- The database test updates task 1, deletes task 2, reinitializes the database to simulate a restart, and proves the updated row remains while the deleted row remains absent.
- The unchanged A1 endpoint assertions prove invalid PUT bodies return JSON 400, unknown IDs return JSON 404, and successful DELETE returns 204 with an empty body.
- UPDATE binds title, boolean, and ID through `?` placeholders; DELETE binds its ID through a `?` placeholder. The application no longer contains an in-memory task list.

## Stage 4 — SQLite exploration

- Installed DB Browser for SQLite 3.13.1 and opened the repository-root `tasks.db` with `docs/stage4.sql`.
- Ran all five required statements. `SELECT COUNT(*) FROM tasks;` returned 3 before the destructive statements: the three seeded tasks.
- After `UPDATE tasks SET done = 1;` followed by `DELETE FROM tasks WHERE done = 1;`, an independent SQLite connection reported `after_required_sql_count=0`, proving DB Browser executed the changes.
- Restored the validated pre-exploration backup; a fresh connection returned `[(1, 'Buy milk', 0), (2, 'Write report', 1), (3, 'Call dentist', 0)]`.

## Stage 5 — Documentation and clean bootstrap

- Moved the existing runtime database aside, ran `python -c "import app.main"`, and confirmed a new repository-root `tasks.db` was created automatically.
- Direct inspection returned exactly `[(1, 'Buy milk', 0), (2, 'Write report', 1), (3, 'Call dentist', 0)]` and columns `id INTEGER PRIMARY KEY`, `title TEXT NOT NULL`, `done INTEGER NOT NULL DEFAULT 0`.
- `python -m pytest -q` → `14 passed in 0.55s` after the documentation changes.
- Captured and visually checked `docs/db-browser.png`; it shows DB Browser for SQLite open on `tasks.db` with the `tasks` table and required schema.

## Test — Full regression and SQL safety

- `python -m pytest -q` → `15 passed in 0.58s`.
- Added an integration test that creates, updates, and deletes through the API while checking the corresponding row directly through a separate SQLite connection after each operation.
- Audited every `SELECT`, `INSERT`, `UPDATE`, and `DELETE` in `app/db.py`. Every request-derived ID, title, and boolean is supplied as a bound argument to a `?` placeholder; no SQL uses interpolation or concatenation.
- Searched `app/` for list assignment/append/remove patterns and found no in-memory task collection.

## Final — Clean clone, restart, and database agreement

- Cloned the committed repository into a new temporary directory and confirmed it contained no `tasks.db`.
- Started it with the README's exact `python -m uvicorn app.main:app --reload` command; health passed and the newly created database contained 3 seeds.
- POST created `{"id":4,"title":"Restart survivor","done":false}`, PUT changed `done` to true, and DELETE of task 1 returned 204.
- Before and after a complete server stop/restart, GET `/tasks` returned the identical state: tasks 2, 3, and 4 with task 4 still done.
- DB Browser ran `docs/final-verify.sql` against that clone with exit code 0. A separate SQLite connection returned `[[2, "Write report", 1], [3, "Call dentist", 0], [4, "Restart survivor", 1]]`, exactly matching the API after boolean conversion.
- Stopped both server process trees and removed the validated temporary clone.

## Push — Public repository delivery

- `git push origin main` updated `https://github.com/tarekamr737/crud-api.git` from `afddfc4` to `3121075`.
- `git ls-remote origin refs/heads/main` returned `3121075aa57e852b81d9cb14caee15f9df05213c`, matching the local FINAL commit before the delivery bookkeeping commit.
- Verified the history contains the required Stage 0 through Stage 5 commit messages followed by dedicated TEST and FINAL commits.
