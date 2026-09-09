# BRIEFING — 2026-09-10T03:50:40+06:00

## Mission
Analyze implementation steps for R3 (Auth & KUET Roll Decoder) and produce structured handoff report.

## 🔒 My Identity
- Archetype: explorer
- Roles: Read-only investigation: analyze problems, synthesize findings, produce structured reports.
- Working directory: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_m1_2
- Original parent: e2f4ecb5-c7a3-43bc-9a0e-1232d8641049
- Milestone: M1 (R3 Auth & KUET Roll Decoder)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Analyze implementation steps for R3 (Auth & KUET Roll Decoder):
  1. Domain validation: require @stud.kuet.ac.bd, reject others with HTTP 400.
  2. Regex extraction of batch, dept, roll from trailing 7 digits of email local part (e.g. siddique52507028 -> Batch=25, Dept=07, Roll=028).
  3. Registration form schema accepting only name, email, password.
  4. User model updates and uniqueness constraints.
  5. Alias GET /api/auth/current.

## Current Parent
- Conversation ID: e2f4ecb5-c7a3-43bc-9a0e-1232d8641049
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `ORIGINAL_REQUEST.md`, `PROJECT.md`
  - `backend/app/routes/auth.py`, `backend/app/auth.py`, `backend/app/models.py`, `backend/app/schemas.py`, `backend/app/main.py`
  - `backend/campus_share.db` SQLite database schema and rows
  - `Tanvir/verify_campus_map.py`, `Tanvir/app.py`, `Tanvir/index.html`
  - `frontend/src/App.jsx`, `frontend/src/context/AuthContext.jsx`
- **Key findings**:
  - Domain validation must return HTTP 400 (not Pydantic's default 422).
  - Trailing 7 digits regex `(\d{2})(\d{2})(\d{3})$` cleanly decodes `batch="25"`, `dept="07"`, `roll="028"`.
  - Registration schema should be updated to `UserRegister(name, email, password)` and frontend inputs for dept/batch/roll removed.
  - `models.User` currently has single-column `unique=True` on `roll`, which causes collisions since multiple students in different batches/departments have the same roll number; must be changed to `UniqueConstraint('batch', 'dept', 'roll')`.
  - SQLite database `campus_share.db` currently lacks `karma` column and has `UNIQUE (roll)`, requiring migration.
  - `GET /api/auth/current` is required by `verify_campus_map.py` without auth headers; must return `{ "authenticated": True, "user": { "roll": ..., "karma": ... } }`.
- **Unexplored areas**: None for R3 scope.

## Key Decisions Made
- Fully formulated architecture and step-by-step implementation code for schemas, models, routes, database migration, and frontend form.
- Documented complete 5-component handoff report in `handoff.md`.

## Artifact Index
- handoff.md — Final analysis and handoff report for R3 implementation
- progress.md — Liveness heartbeat and milestone progress
- DISPATCH.md — Initial dispatch message
