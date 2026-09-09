# BRIEFING — 2026-09-09T22:03:00Z

## Mission
Implement Milestone 1 (Backend Core, Migration & Karma Implementation) for KUET MANTIS.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/worker_m1
- Original parent: e2f4ecb5-c7a3-43bc-9a0e-1232d8641049
- Milestone: Milestone 1

## 🔒 Key Constraints
- Exclusive file ownership: backend/app/data/kuet_landmarks.json, backend/app/routes/landmarks.py, backend/app/routes/auth.py, backend/app/routes/items.py, backend/app/routes/borrow_requests.py, backend/app/routes/transactions.py, backend/app/models.py, backend/app/schemas.py, backend/app/main.py, backend/app/database.py, backend/app/seed.py, backend/test_m1.py.
- Delete orphaned backend/app/routes/requests.py.
- Do NOT touch frontend files in this milestone.
- No shortcuts, mock/fake tests, or facade logic. Genuine implementations required.
- SQLite migration safeguards must ensure existing DB tables are upgraded with missing columns.

## Current Parent
- Conversation ID: e2f4ecb5-c7a3-43bc-9a0e-1232d8641049
- Updated: 2026-09-09T22:03:00Z

## Task Summary
- **What to build**: Landmarks API, KUET Roll Decoder & Domain Enforcer, Karma Protocol (+10 owner, +5 on-time borrower, -30 late borrower), Item model extensions (type, specs, tags, coords), request status update fixes, database migration and seeding.
- **Success criteria**: All automated verification tests pass, server boots cleanly, schemas and routes conform to frontend expectations.
- **Interface contracts**: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/PROJECT.md
- **Code layout**: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/PROJECT.md § Code Layout

## Key Decisions Made
- Port Tanvir/kuet_data/kuet_landmarks.json to backend/app/data/kuet_landmarks.json and serve via GET /api/landmarks and /api/landmarks/.
- Implemented migrate_db() in database.py to dynamically upgrade existing SQLite databases (adding karma, type, specs, tags, status, zone_id, and composite unique constraint).
- Anchored relative SQLite database path to backend/ directory for uniform execution from any working directory.
- Built robust in-process ASGI test client for isolated end-to-end verification.

## Artifact Index
- /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/worker_m1/DISPATCH.md — Task assignment and specs
- /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/worker_m1/BRIEFING.md — Situational awareness and state
- /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/worker_m1/progress.md — Liveness heartbeat
- /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/worker_m1/handoff.md — Final Milestone 1 handoff report
- /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend/test_m1.py — Comprehensive automated test suite

## Change Tracker
- **Files modified**:
  - `backend/app/data/kuet_landmarks.json`: 21 zones and 10 sample active items ported.
  - `backend/app/routes/landmarks.py`: GET /api/landmarks and /api/landmarks/ endpoint.
  - `backend/app/models.py`: User karma, composite uniqueness on (batch, dept, roll); Item type, specs, tags, status, zone_id.
  - `backend/app/schemas.py`: UserRegister, UserOut karma, TransactionOut, BorrowRequestOut.transaction, ItemOut normalization.
  - `backend/app/routes/auth.py`: KUET domain check (@stud.kuet.ac.bd), roll regex decoder, 100 karma init, GET /api/auth/current alias.
  - `backend/app/routes/transactions.py`: KUET Karma (+10 owner, +5 on-time borrower, -30 late borrower).
  - `backend/app/routes/borrow_requests.py`: Accept status from JSON body or query param ?status=...
  - `backend/app/routes/items.py`: JSON & multipart form support, rich filtering (type, category, q, zone).
  - `backend/app/database.py`: migrate_db() schema migration and path anchoring.
  - `backend/app/seed.py`: 8 student accounts and 10 campus items seeded.
  - `backend/app/main.py`: Landmarks router mounted, migrate_db and seed_db triggered on startup.
  - `backend/app/auth.py`: Added get_current_user_optional and bearer_scheme_optional.
  - `backend/app/routes/requests.py`: Deleted orphaned file.
  - `backend/test_m1.py`: Created comprehensive verification script.
- **Build status**: PASS (All 6 test suites and 95 Tanvir tests passing 100%)
- **Pending issues**: None

## Quality Status
- **Build/test result**: PASS (100%)
- **Lint status**: 0 violations
- **Tests added/modified**: backend/test_m1.py (all M1 requirements verified)

## Loaded Skills
- None
