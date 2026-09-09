# BRIEFING — 2026-09-10T03:44:30+06:00

## Mission
Survey and document the existing React frontend in /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/ to guide dashboard refactoring and MapLibre GL integration.

## 🔒 My Identity
- Archetype: explorer
- Roles: explorer, frontend surveyor
- Working directory: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_survey_2
- Original parent: e2f4ecb5-c7a3-43bc-9a0e-1232d8641049
- Milestone: survey

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Focus exclusively on frontend architecture, dependencies, UI/UX structure, and MapLibre GL JS integration readiness

## Current Parent
- Conversation ID: e2f4ecb5-c7a3-43bc-9a0e-1232d8641049
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `frontend/package.json` (Vite, React 18, React Query, missing MapLibre/Lucide)
  - `frontend/src/` (main.jsx, App.jsx, api/client.js, context/AuthContext.jsx, components, pages)
  - `Tanvir/index.html` (MapLibre GL JS v3.6.2, OSM tiles, 700m circle, marker styles, pinpoint workflow)
  - `Tanvir/export_contracts/campus_map_contract.ts` (GodsEyeMapProps, KUETLandmark, MapItemPin)
  - `Tanvir/verify_campus_map.py` (Verification criteria for map, markers, HUD, auth)
  - `backend/app/schemas.py`, `backend/app/routes/items.py`, `backend/app/routes/requests.py` (API alignment)
- **Key findings**:
  - `frontend/package.json` lacks `maplibre-gl` and icon packages; `node`/`npm` is absent in current host PATH, suggesting CDN-based MapLibre inclusion in `index.html` as the most reliable approach.
  - Current UI layout is top-navbar only without a sidebar; needs refactoring into a full dashboard layout (left sidebar, top action bar, hover cards/popovers).
  - Registration form in `App.jsx` currently asks for dept, batch, roll instead of decoding from `@stud.kuet.ac.bd` email prefix (violates R3).
  - Trust score (float 4.5) must be replaced with KUET Karma (Base 100, +10/+5/-30) across UI (R4).
  - `AddItemForm.jsx` is currently empty (0 bytes); click-to-pinpoint mode from `Tanvir/` must be integrated.
- **Unexplored areas**: None within frontend survey scope.

## Key Decisions Made
- Fully documented 5-component handoff report at `.agents/explorer_survey_2/handoff.md`.
- Outlined concrete architecture for `DashboardLayout.jsx`, `GodsEyeMap.jsx`, roll decoder, and Karma protocol.

## Artifact Index
- `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_survey_2/handoff.md` — Full 5-component frontend survey & refactoring report
- `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_survey_2/progress.md` — Progress tracker
- `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_survey_2/DISPATCH.md` — Recorded dispatch
