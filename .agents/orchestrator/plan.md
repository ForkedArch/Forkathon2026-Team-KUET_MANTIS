# Plan: CampusShare KUET

## Objective
Execute the integration, UI layout upgrade, KUET authentication/roll decoder, KUET karma protocol, and automated evaluation loop for CampusShare KUET to achieve >= 18/20 on the rubric.

## Roadmap & Milestones
1. **Survey (Step 0)**:
   - Spawn 3 Explorers in parallel:
     - Explorer 1: Inspect `Tanvir/` (index.html, app.py, kuet_data, map/UI logic, endpoints).
     - Explorer 2: Inspect `frontend/` (React structure, package.json, dependencies, map support, router/views).
     - Explorer 3: Inspect `backend/` (FastAPI structure, models, schemas, auth, routers, database/storage).
   - Synthesize findings into `PROJECT.md` with Feature Inventory, Architecture, Interface Contracts, and Milestones.

2. **Milestone 1 (R1) - Architecture Integration & Cleanup**:
   - Port MapLibre map and UI logic from `Tanvir/index.html` into React `frontend/`.
   - Move data and endpoints from `Tanvir/app.py` and `Tanvir/kuet_data/` into FastAPI `backend/`.
   - Delete `Tanvir/` directory completely once integration is verified.

3. **Milestone 2 (R2) - UI Layout & Design (Dashboard Style)**:
   - Dashboard layout with left sidebar (Map View, My Items, Requests, Profile).
   - Top action bar (Add Item), search/filter bar, clean tables/lists.
   - Hover cards / popovers for item details and mini-map locations.
   - Clean, light theme with subtle accents.

4. **Milestone 3 (R3) - Authentication & KUET Roll Decoder**:
   - Registration accepts Full Name, Password, and Email (`@stud.kuet.ac.bd` only).
   - Backend automatic parser for Batch, Department, Roll from prefix (e.g., `siddique52507028@stud.kuet.ac.bd` -> Batch=25, Dept=07, Roll=028).
   - Rejection of non-KUET emails with appropriate error.

5. **Milestone 4 (R4) - KUET Karma Protocol**:
   - Replace 5.0 trust score with KUET Karma Rating System (100 base karma).
   - Lending adds +10 to owner on complete.
   - Returning on time adds +5 to borrower.
   - Returning late deducts -30.
   - Transaction flows and frontend display.

6. **Milestone 5 (R5) - Automated Evaluation Loop & Testing**:
   - Verify full end-to-end flow: Add Item -> View on Map/List -> Request -> Accept -> Handover -> Return.
   - Agent-as-Judge evaluation on 20-point rubric (Integration: 4, UI: 4, Auth: 4, Karma: 4, E2E: 4) >= 18/20.
   - Victory audit verification.
