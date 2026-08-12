# TASKS.md

## A4 — Auth · Login & Protect

- [x] Inspect existing FastAPI app; preserve CRUD/database behavior.
- [x] Add Supabase dependency + `.env.example`; ensure `.env` is ignored.
- [x] Configure Supabase client using URL + anon key only.
- [x] Add signup → 201/400.
- [x] Add login → 200 tokens / 400 / 401.
- [x] Add `/public/info` → 200.
- [x] Add reusable `HTTPBearer` + `get_current_user`.
- [x] Verify JWT using Supabase `get_user(token)`.
- [x] Add `/protected/profile` → 200; bad/missing token → 401.
- [x] Add second protected route using same dependency.
- [ ] Add protected logout → 204.
- [ ] Verify Swagger `/docs` Authorize + protected-route locks.
- [ ] Test valid, missing, malformed, expired/tampered token flows.
- [ ] Run regression checks for existing CRUD API.
- [ ] Confirm `.env` and secrets never entered git history.
- [ ] Update README: setup, env, run, endpoints, auth, Swagger screenshot.
- [ ] Run final end-to-end signup → login → protected → tampered-token test.
- [ ] Ensure ≥6 meaningful stage commits and push.
