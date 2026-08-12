# TASKS.md

- [x] S0 Inspect A2; add `.gitignore`; run Postgres container + named volume; verify `psql`; commit `Stage 0: Postgres in Docker + gitignore`
- [x] S1 Add `.env`/`.env.example`; install psycopg; swap SQLite repository for Postgres connection/schema/seed-once; verify 3 rows after 3 restarts; commit `Stage 1: connect via .env and create table`
- [x] S2 Move GET storage to parameterized Postgres SELECTs; preserve 200/404; commit `Stage 2: read from Postgres`
- [x] S3 Move POST/PUT/DELETE to parameterized Postgres SQL; preserve 201/200/204/400/404; commit `Stage 3: full CRUD on Postgres`
- [x] S4 Add minimal `Dockerfile` + `compose.yaml` with `api` + `db` + named volume; API uses host `db`; verify `docker compose up`; commit `Stage 4: docker-compose the whole stack`
- [ ] S5 Update README with env setup/one-command run/endpoints/curl/DB screenshot; verify clean clone; commit `Stage 5: one-command stack + docs`
- [ ] TEST Re-run A1/A2 contract tests; verify no interpolated SQL and `.env` absent from Git
- [ ] FINAL Create tasks -> `docker compose down` -> `docker compose up` -> confirm persistence + direct Postgres rows
- [ ] PUSH Push same public repo; confirm honest stage commits
- [ ] OPTIONAL Only after FINAL: DB healthcheck/index/Redis/multi-stage image/mortality experiment
