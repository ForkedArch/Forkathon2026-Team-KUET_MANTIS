# Soft Handoff: Project Orchestrator (Generation 1 -> Generation 2)

**Timestamp**: 2026-09-09T22:22:00Z  
**Predecessor**: Generation 1 Orchestrator (`e2f4ecb5-c7a3-43bc-9a0e-1232d8641049`)  
**Parent**: Sentinel (`dad442f2-c7ca-424c-8bb8-47aafb24c35e`)  
**Workspace**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS`  
**Working Directory**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/orchestrator`

---

## 1. Milestone State

| # | Milestone Name | Status | Summary & Verification |
|---|----------------|--------|------------------------|
| M0 | Survey & Architecture | **DONE** | 3 survey explorers mapped Tanvir, frontend, backend. `PROJECT.md` created with 24-feature inventory & contracts. |
| M1 | Backend Core & Data Migration | **DONE** | 21 landmarks ported; `/api/landmarks` implemented; R3 Roll Decoder active; R4 KUET Karma (+10, +5, -30) active; state machine replay, OTP clearing, concurrency race protection, and validation hardening complete. All 4 test suites passing (`test_m1.py`, `test_adversarial_karma.py`, `test_adversarial_challenger.py`, `verify_campus_map.py`). Auditor verdict: `CLEAN`. Gate: **PASS**. |
| M2 | Frontend Dashboard & MapLibre Integration | **EXPLORATION DONE / READY FOR IMPLEMENTATION** | 3 specialized explorers (`explorer_m2_1`, `explorer_m2_2`, `explorer_m2_3`) completed complete, production-ready code templates for MapLibre canvas (`GodsEyeMap.jsx`), Dashboard Shell (`DashboardLayout.jsx`, `Sidebar.jsx`, `TopActionBar.jsx`), Popovers (`ItemHoverCard.jsx`), AddItem Modal (`AddItemModal.jsx`), and 3-field Auth (`Register.jsx`). |
| M3 | End-to-End Integration & Cleanup | **PLANNED** | Integration verification; delete `Tanvir/` folder completely. |
| M4 | Automated Evaluation Loop & Judge Scoring | **PLANNED** | Implement `judge_rubric.py` (20-pt rubric) and iterate until score >= 18/20. |
| M5 | Final Victory Verification | **PLANNED** | Victory audit & final completion report to sentinel. |

---

## 2. Active Subagents
All 16 subagents from Generation 1 have completed their tasks and delivered reports. No subagents are currently running.

---
## 3. Pending Decisions & Architecture Instructions for Successor

1. **Immediate Next Step**:
   Spawn `worker_m2` to implement Milestone 2 (Frontend Dashboard & MapLibre Integration) using the comprehensive templates from:
   - `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_m2_1/handoff.md` (MapLibre GL JS v3.6.2, OSM raster tiles, 700m perimeter circle, emerald lend markers, radar pulsing borrow beacons, click-to-pinpoint mode, bottom-right HUD controls).
   - `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_m2_2/handoff.md` (DashboardLayout, Left Sidebar with KUET branding and student Karma card, Top Action Bar with search/category/type toggle, AllItems view).
   - `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_m2_3/handoff.md` (ItemHoverCard popovers, AddItemModal with click-to-pinpoint, 3-field Registration with live roll decoding, Karma displays across views).

2. **Frontend Dependencies Rule**:
   - `node` / `npm` are not in the host PATH.
   - Include MapLibre GL JS v3.6.2 and CSS via unpkg CDN tags in `frontend/index.html` (matching `Tanvir/index.html` lines 9-10).
   - Use clean, self-contained inline SVGs (already fully authored in `explorer_m2_2/handoff.md`) to avoid uninstalled `lucide-react` dependency.

3. **Verification Panel for M2**:
   After `worker_m2` completes, dispatch 2 Reviewers, 2 Challengers, and 1 Auditor (`teamwork_preview_auditor`) to evaluate M2 before gating.

4. **Milestone 3 Cleanup**:
   Once M2 passes, test the full user flow and delete `Tanvir/` (`rm -rf Tanvir/`).

5. **Milestone 4 Rubric Evaluation**:
   Implement `judge_rubric.py` (20-point rubric: 4 pts Integration, 4 pts UI, 4 pts Auth, 4 pts Karma, 4 pts E2E) and run until score >= 18/20.

---

## 4. Key Artifacts
- `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/ORIGINAL_REQUEST.md` — Authoritative user request
- `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/PROJECT.md` — Authoritative project index & contracts
- `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/orchestrator/GATE_STATUS.md` — M1 gate pass record
- `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_m2_1/handoff.md` — MapLibre component code
- `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_m2_2/handoff.md` — Dashboard layout code
- `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_m2_3/handoff.md` — Hover cards & auth code
