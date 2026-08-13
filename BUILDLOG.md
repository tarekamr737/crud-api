# Build Log

## Async triage jobs

- Used the existing PostgreSQL service as the durable queue and added one separate worker process instead of introducing Redis/Celery. This keeps submission fast while making state survive API restarts.
- Required a client-provided `Idempotency-Key`; the database returns the original job only when its request hash matches, and rejects key reuse for different input with 409.
- Used expiring leases plus lease-token-guarded updates because queue delivery is intentionally at least once. A stale worker may finish, but it cannot overwrite a result after another worker has reclaimed the job.
- Kept terminal alerts as safe structured stdout events for the deployment log/alert pipeline; neither user text nor provider exception detail is included.
- Replaced the pre-existing Docker-managed PostgreSQL volume with `./.data/postgres`, an ignored bind mount under the D: workspace, so material runtime data does not consume the full C: partition.
- `docker compose config` expanded the ignored `.env` into diagnostic output, including the OpenRouter credential. No value entered a file or Git, but the key must be rotated because session output is exposure. Restricted the database to PostgreSQL settings and the worker to database/LLM settings so neither receives unrelated secrets.
- The first D:-backed PostgreSQL initialization produced localhost-only `pg_hba.conf` rules, so worker/API containers were rejected. Set `POSTGRES_HOST_AUTH_METHOD=scram-sha-256` for password-authenticated Compose-network access and reinitialized only the disposable database created for this verification.

## Week 7 Final audit

- A literal Git pickaxe search for `sk-or-v1-` initially matched the audit wording in `EVIDENCE.md`, not a credential. Rechecked current and historical diffs with a key-shaped regex requiring at least ten suffix characters; both were clean.
- Avoided Docker for the clean-snapshot proof because its engine storage could use the full C: partition. Exported committed `HEAD` under the repository's ignored `.tmp`, and redirected the fresh environment, pip cache, pytest base temp, `TEMP`, and `TMP` to D:.

## Week 7 Stage 5

- Scored only the three routing fields (`category`, `urgency`, `suggested_team`) across exactly eight hand-labelled cases; confidence and prose remain validated API fields but are not treated as exact-match classification labels.
- The real eval encountered transient free-pool failures on three attempts, all recovered inside the production retry policy. The final result was 24/24 with no evaluator-side retry loop.
- Added `python-dotenv` only so the standalone eval runner and Uvicorn's documented `--env-file` workflow can consume the ignored local configuration; Docker Compose continues to inject the same variables with `env_file`.
- The configured remote redirected from its legacy `crud-api` URL to the canonical `Back-End-AI-Engineering-FlyRank-Intern` repository. Kept the configured remote intact because Git followed the redirect safely and GitHub resolved the canonical PR target.

## Week 7 Stage 4

- Centralized `triage-v1`, the 30-second timeout, and the three-attempt limit in immutable configuration. The client logs each actual HTTP attempt before any retry sleep so `duration_ms` measures provider-call time rather than backoff time.
- `Retry-After` is treated as a minimum delay over exponential 1s/2s backoff plus jitter. General connection/configuration errors and HTTP 400/401/403 fail immediately; only timeout, 429, and 5xx enter the loop.

## Week 7 Stage 3

- Kept parse/schema errors as safe field/type summaries that exclude invalid input values. The repair request contains the broken output and that safe error as JSON-encoded user data, while HTTP responses expose only a fixed 422 message.
- Quarantine records bound user text to 500 characters and raw completion text to 2,000 characters, replace non-printable input characters, and remain ignored JSONL runtime artifacts under `logs/`.

## Week 7 Stage 1

- Scoped field-specific validation errors to `/triage` so the new contract names `text` or an unexpected field without changing the established CRUD/auth `{"error":"Invalid request"}` behavior.
- Kept the unfinished real-model branch behind a safe 503 while Stage 1 exercises only `LLM_STUB=1`; the provider method is patched in tests to prove stub and invalid-input paths make zero model calls.

## Week 7 Stage 2

- The first real triage checkpoint received a transient HTTP-success response with `choices=null`; a bounded diagnostic retry returned choices normally. Added an explicit missing-content guard so this provider shape becomes a safe service failure instead of a `TypeError`.
- The selected free model twice returned upstream shared-pool 429 errors during the three-input checkpoint. Kept the required model, used bounded manual retries, and honored the provider's explicit 24-second retry interval; all three inputs then passed.

## Week 7 Stage 0

- Used the user-selected `google/gemma-4-26b-a4b-it:free` model instead of the architecture document's older `openrouter/free` placeholder.
- The first live checkpoint reached OpenRouter but returned 401 because the manually loaded `.env` value retained its surrounding quotes. Stripping dotenv-style quotes in process memory sent the authentication header correctly; the retry returned exactly `ready`.

## W5 A9 — Global skill promotion

- Installed fresh official skills from `supabase/agent-skills` instead of
  copying the locked repository snapshots because their hashes differed; both
  current upstream versions validated successfully before the local copies
  were removed.

## W5 A9 — Live encoding correction

- The first full live run fetched/cached all 60 detail pages but normalized
  zero records because `requests` defaulted the target's charset-less HTML to
  ISO-8859-1, turning the UTF-8 pound bytes into `U+00C2 U+00A3`. The run
  honestly reported 60 page failures instead of storing bad data.
- The designated site serves UTF-8 HTML, so successful responses now set UTF-8
  before reading `.text`. Repaired the already cached HTML in place from the
  reversible Latin-1 mojibake to UTF-8 rather than making 63 unnecessary repeat
  requests.

## W5 A9 — Canonical idempotency

- Chose stable first-seen wins for duplicate `product_url` candidates because
  catalogue discovery order is deterministic and duplicate detail pages should
  never be fetched or allowed to overwrite earlier provenance.

## W5 A9 — HTML cache

- Pytest does not create a missing parent of `--basetemp` on this Windows
  setup. Created the ignored `scraper/.tmp/` directory on `D:` before rerunning
  so no test artifacts use the full `C:` drive.

## W5 A9 — Target classification

- The target has no published `/robots.txt` file (HTTP 404). Treated that as
  an absence of site-specific directives, not as permission to crawl broadly;
  the implementation remains limited to the specified 3 + 60 pages and the
  stricter assignment politeness rules.

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
- A later Chrome DevTools MCP session became available, so the stale screenshot was replaced with a live `/docs` capture and the README documentation checkpoint was completed.
- The authenticated Supabase MCP tool set can inspect docs, project metadata, database state, advisors, and logs, but does not expose hosted Auth provider configuration. It confirmed `email_not_confirmed`; disabling confirmation remains a Dashboard-only step for this project.

## A4 Final

- Used the user-disabled Confirm Email setting for the assignment's immediate signup-to-login acceptance flow. Supabase remains the sole password and identity manager; the application configuration and token verification code did not require a workaround or privileged key.
- The first final regression attempt stopped during collection because the shell had not loaded the ignored Supabase settings. Loaded only `SUPABASE_URL` and `SUPABASE_KEY` from `.env` into the retry's process environment; the unchanged suite then passed all 33 tests.

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
