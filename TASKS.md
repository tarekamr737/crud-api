# TASKS.md

- [x] S0 Inspect A1; add SQLite init/table/seed-if-empty; restart 3x -> exactly 3; commit `Stage 0: create SQLite database`
- [x] S1 Replace GET storage with parameterized SELECTs; keep 200/404 contract; commit `Stage 1: database read endpoints`
- [x] S2 Replace POST storage with INSERT; SQLite ID; persist after restart; keep 400/201; commit `Stage 2: insert into database`
- [ ] S3 Replace PUT/DELETE with parameterized UPDATE/DELETE; keep 400/404/204; verify restart; commit `Stage 3: update and delete with SQL`
- [ ] S4 Open `tasks.db` in DB Browser; run required SQL; record 1 query + observation; commit `Stage 4: explored SQLite`
- [ ] S5 Update `.gitignore` + README; add DB screenshot; verify clean DB auto-creates + seeds; commit `Stage 5: database documentation`
- [ ] TEST Re-run all A1 endpoint tests + DB persistence tests; verify no request input is interpolated into SQL
- [ ] FINAL Full CRUD -> restart -> same state; DB Browser matches API; clean clone starts with one documented command
- [ ] PUSH Push updated same public repo; verify honest stage commits
- [ ] OPTIONAL Only after FINAL: search/filter/sort/stats/timestamps/index/transaction
