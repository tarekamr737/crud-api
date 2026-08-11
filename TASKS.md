# TASKS.md

- [x] S0 Scaffold FastAPI; `GET /` hello; run; commit `Stage 0: hello server`
- [x] S1 Add required `/` metadata + `/health`; verify 200; commit `Stage 1: root and health endpoints`
- [x] S2 Seed 3 tasks; add GET list/single + 404 JSON; commit `Stage 2: read endpoints with 404`
- [ ] S3 Add POST; next ID; `done=false`; 201; invalid title → 400; commit `Stage 3: create with validation`
- [ ] S4 Add PUT + DELETE; 400/404; DELETE 204 empty; run full CRUD; commit `Stage 4: full CRUD`
- [ ] S5 Add endpoint docs; verify `/docs` + Swagger CRUD; save screenshot; commit `Stage 5: Swagger UI`
- [ ] S6 Add focused tests + README + requirements; run `pytest -q`; verify clean-start instructions
- [ ] S6 Publish public GitHub repo; ensure ≥6 honest commits; commit `Stage 6: publish and docs`
- [ ] FINAL Re-run curl CRUD flow; verify `200/201/204/400/404`; remove dead/out-of-scope code
