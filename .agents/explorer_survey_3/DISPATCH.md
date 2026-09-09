# Dispatch: Explorer Survey 3 (Backend Architecture & Evaluation)

## Objective
Survey and document the existing FastAPI backend and evaluation infrastructure in `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend/` and project root.
Analyze:
1. `backend/`: FastAPI application structure, routers, models, schemas, database (SQLite/PostgreSQL/in-memory), dependencies (`pyproject.toml` or `requirements.txt`).
2. Current Auth system: registration endpoint, password hashing, token generation, user model (fields: name, email, karma/trust_score, batch, dept, roll).
3. Current Borrow/Lending/Transaction system: item creation, request, accept, handover, return, karma deduction/addition.
4. Existing evaluation / test scripts: look for any judge scripts, rubric evaluators, test suites, or benchmarks in the repository.
5. Endpoints needed from `Tanvir/app.py` and static data (`kuet_data/`) to be ported into `backend/`.

## Input Files
- `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/ORIGINAL_REQUEST.md` (Mandatory read)
- All files in `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend/`
- Any root-level evaluation/test files

## Output
Write your findings to `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_survey_3/handoff.md` with:
- Backend architecture, models, database schemas, router mappings
- Required changes for R1 (Tanvir endpoints/data), R3 (KUET email roll decoder), R4 (Karma protocol: 100 base, +10 lending, +5 return on time, -30 late return)
- Evaluation infrastructure and Judge requirements (R5: 20-point rubric)

## 2026-09-09T21:40:58Z
You are explorer_survey_3.
Your working directory is: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_survey_3
Your dispatch file is: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_survey_3/DISPATCH.md
MANDATORY: Read /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/ORIGINAL_REQUEST.md before starting work.

Your task:
Survey and document the existing FastAPI backend and evaluation infrastructure in /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend/ and project root.
Examine:
1. backend/: FastAPI application structure, routers, models, schemas, database (SQLite/PostgreSQL/in-memory), dependencies (pyproject.toml / requirements.txt).
2. Current Auth system: registration endpoint, password hashing, token generation, user model (fields: name, email, karma/trust_score, batch, dept, roll).
3. Current Borrow/Lending/Transaction system: item creation, request, accept, handover, return, karma deduction/addition.
4. Existing evaluation / test scripts: look for any judge scripts, rubric evaluators, test suites, or benchmarks in the repository.
5. Endpoints needed from Tanvir/app.py and static data (kuet_data/) to be ported into backend/.

Write your full findings and handoff report to:
/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_survey_3/handoff.md
Update your progress.md periodically.
When done, report back with send_message to the parent.
