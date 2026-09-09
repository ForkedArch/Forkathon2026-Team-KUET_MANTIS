# BRIEFING — 2026-09-09T22:28:30Z

## Mission
Orchestrate the full implementation, integration, testing, and evaluation of CampusShare KUET to achieve >= 18/20 on the rubric.

## 🔒 My Identity
- Archetype: project_orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/orchestrator
- Original parent: dad442f2-c7ca-424c-8bb8-47aafb24c35e
- Original parent conversation ID: dad442f2-c7ca-424c-8bb8-47aafb24c35e

## 🔒 My Workflow
- **Pattern**: Project
- **Scope document**: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/PROJECT.md
1. **Decompose**: Survey (3 explorers) -> Feature Inventory & Architecture in PROJECT.md -> Milestones (M1 to M5)
2. **Dispatch & Execute** (pick ONE):
   - **Direct (iteration loop)**: Explorer (3) -> Worker (1) -> Reviewer (2) + Challenger (2) + Auditor (1) -> Gate
3. **On failure** (in this order):
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
   - Escalate: report to parent (sub-orchestrators only, last resort)
4. **Succession**: Self-succeed at 16 spawns
- **Work items**:
  1. Survey and project decomposition [done]
  2. M1: Backend Core & Data Migration [done]
  3. M2: Frontend Dashboard & MapLibre [verification running]
  4. M3: End-to-End Integration & Cleanup [pending]
  5. M4: Automated Evaluation Loop & Judge Rubric [pending]
  6. M5: Final Victory Verification [pending]
- **Current phase**: 2B (M2 Verification Panel)
- **Current focus**: Milestone 2 verification panel (reviewer_m2_1, reviewer_m2_2, challenger_m2_1, challenger_m2_2, auditor_m2_1)

## 🔒 Key Constraints
- DISPATCH-ONLY orchestrator: NEVER write, modify, or create source code files directly.
- NEVER run build/test commands yourself — require workers to do so.
- NEVER investigate or explore the problem at the code level — dispatch Explorers.
- Write only to .agents/orchestrator/.
- Never reuse a subagent after it has delivered its handoff — always spawn fresh.
- Binary veto on integrity violations.

## Current Parent
- Conversation ID: dad442f2-c7ca-424c-8bb8-47aafb24c35e
- Updated: not yet

## Key Decisions Made
- Milestone 1 GATE PASSED.
- Milestone 2 implementation completed by worker_m2.
- Milestone 2 verification panel dispatched.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| worker_m2 | teamwork_preview_worker | M2 Frontend Implementation | completed | 9270eb17-6083-4535-976c-6c15d8985ea2 |
| reviewer_m2_1 | teamwork_preview_reviewer | M2 MapLibre Component Review | in-progress | 9dc8ae6e-0a0d-456f-86d0-cff3b706fdd9 |
| reviewer_m2_2 | teamwork_preview_reviewer | M2 Dashboard & Auth Review | in-progress | 9a91feaf-daa0-4637-aa84-9bf9690aa7c0 |
| challenger_m2_1 | teamwork_preview_challenger | M2 MapLibre Stress Testing | in-progress | c4a5ba24-e395-43ea-9cc9-ed8d28cb9de0 |
| challenger_m2_2 | teamwork_preview_challenger | M2 Auth & Karma UI Stress Testing | in-progress | 4d9e92be-150c-499f-b0ff-030c2890c3e4 |
| auditor_m2_1 | teamwork_preview_auditor | M2 Forensic Integrity Audit | in-progress | 4cee3874-6576-4007-8d17-25ba86fdf16c |

## Active Timers
- Heartbeat cron: task-227
- Safety timer: none

## Artifact Index
- /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/PROJECT.md — Global project architecture, feature inventory, milestones
- /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/ORIGINAL_REQUEST.md — Original User Request
- /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/orchestrator/GATE_STATUS.md — Gate verdicts
- /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/orchestrator/BRIEFING.md — Persistent memory
- /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/orchestrator/progress.md — Progress & liveness heartbeat
