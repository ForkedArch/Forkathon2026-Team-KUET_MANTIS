# BRIEFING — 2026-09-09T21:46:00Z

## Mission
Survey and document the FastAPI backend, Auth, Karma protocol, Tanvir porting requirements, and evaluation/test infrastructure.

## 🔒 My Identity
- Archetype: explorer
- Roles: explorer, survey, synthesis
- Working directory: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_survey_3
- Original parent: e2f4ecb5-c7a3-43bc-9a0e-1232d8641049
- Milestone: survey

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Output handoff report to /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_survey_3/handoff.md
- Verify all file paths and exact code lines directly

## Current Parent
- Conversation ID: e2f4ecb5-c7a3-43bc-9a0e-1232d8641049
- Updated: 2026-09-09T21:46:00Z

## Investigation State
- **Explored paths**: `backend/` (main.py, models.py, schemas.py, auth.py, database.py, routes/*, utils/*), `Tanvir/` (app.py, verify_campus_map.py, kuet_data/kuet_landmarks.json, export_contracts/campus_map_contract.ts, index.html), `frontend/` (App.jsx, client.js, Requests.jsx, Transaction.jsx, AddItem.jsx, Home.jsx, Profile.jsx).
- **Key findings**:
  1. R1: `kuet_landmarks.json` (21 zones, 700m radius, 10 items) and endpoints (`GET /api/landmarks`, `GET /api/items`, `POST /api/items`, `GET /api/auth/current`) must be integrated into `backend/`.
  2. R3: Registration currently requires manual dept/batch/roll. Must update to regex `(\d{2})(\d{2})(\d{3})$` from email ending in `@stud.kuet.ac.bd`.
  3. R4: Karma rating system requires 100 base karma, +10 for lender, +5 for on-time borrower, -30 for late borrower.
  4. R5: No 20-point rubric evaluator exists yet (only older 10-point `Tanvir/verify_campus_map.py`). A 20-point Judge script must be created.
  5. Critical bugs found: `BorrowRequestOut` missing `transaction` field, `borrow_requests.py` PUT status body/query mismatch, `items.py` POST form vs JSON mismatch, orphaned `requests.py`, and Windows artifacts in `backend/venv`.
- **Unexplored areas**: None within backend survey scope.

## Key Decisions Made
- Survey completed and verified against actual codebase.
- Comprehensive 5-component handoff report generated at `.agents/explorer_survey_3/handoff.md`.

## Artifact Index
- `.agents/explorer_survey_3/DISPATCH.md` — task instructions
- `.agents/explorer_survey_3/progress.md` — progress heartbeat
- `.agents/explorer_survey_3/BRIEFING.md` — working memory
- `.agents/explorer_survey_3/handoff.md` — final survey report
