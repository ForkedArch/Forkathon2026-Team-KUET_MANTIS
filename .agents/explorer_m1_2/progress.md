# Progress — explorer_m1_2

Last visited: 2026-09-10T03:50:00+06:00

## Completed Tasks
- [x] Read ORIGINAL_REQUEST.md and PROJECT.md thoroughly.
- [x] Investigated backend auth routes (`backend/app/routes/auth.py`), models (`backend/app/models.py`), schemas (`backend/app/schemas.py`), and helper modules (`backend/app/auth.py`).
- [x] Investigated Tanvir verification tests (`Tanvir/verify_campus_map.py`) and legacy mock server (`Tanvir/app.py`).
- [x] Analyzed database schema in `backend/campus_share.db` (`users` table, constraints, existing rows).
- [x] Identified SQLite schema limitation: `users` table lacks `karma` column and contains hardcoded `UNIQUE (roll)` constraint that must be migrated.
- [x] Defined complete 5-component architecture analysis for R3:
  1. Domain validation (@stud.kuet.ac.bd, HTTP 400 rejection).
  2. Regex extraction of batch, dept, roll from trailing 7 digits (`r'(\d{2})(\d{2})(\d{3})$'`).
  3. Registration form schema updates (Pydantic `UserRegister` accepting only name, email, password, and frontend form refactor).
  4. User model updates (`karma: int = 100`, composite unique constraint `(batch, dept, roll)`, SQLite migration plan).
  5. Implementation specification for alias `GET /api/auth/current` supporting unauthenticated test calls and authenticated sessions.

## Current Task
- Compiling final 5-component handoff report (`handoff.md`).
