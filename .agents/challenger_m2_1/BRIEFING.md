# BRIEFING — 2026-09-10T04:28:30+06:00

## Mission
Adversarially challenge Milestone 2 frontend integration: MapLibre/Turf fallback, coordinate pinpointing boundaries, HUD controls, package import safety, and Tanvir/verify_campus_map.py.

## 🔒 My Identity
- Archetype: EMPIRICAL CHALLENGER
- Roles: critic, specialist
- Working directory: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/challenger_m2_1
- Original parent: e2f4ecb5-c7a3-43bc-9a0e-1232d8641049
- Milestone: Milestone 2 (Frontend Integration)
- Instance: 1 of 1

## 🔒 Key Constraints
- Review-only — do NOT modify implementation code directly
- Must run verification code directly; do not trust worker claims without empirical proof
- Test MapLibre fallback behavior when Turf.js is not yet loaded
- Test coordinate pinpointing boundary values and HUD control events
- Test that no missing package imports crash components
- Run python3 Tanvir/verify_campus_map.py
- Report explicit verdict: APPROVE or REQUEST_CHANGES in handoff.md

## Current Parent
- Conversation ID: e2f4ecb5-c7a3-43bc-9a0e-1232d8641049
- Updated: not yet

## Review Scope
- **Files to review**: Frontend campus map implementation, worker_m2 changes, Tanvir/verify_campus_map.py
- **Interface contracts**: ORIGINAL_REQUEST.md, PROJECT.md
- **Review criteria**: Correctness, resilience to missing dependencies (Turf), boundary behavior, import safety, test suite pass

## Attack Surface
- **Hypotheses tested**: [TBD]
- **Vulnerabilities found**: [TBD]
- **Untested angles**: [TBD]

## Loaded Skills
- None

## Key Decisions Made
- Initializing empirical challenge suite

## Artifact Index
- DISPATCH.md — Dispatch instructions
- BRIEFING.md — Persistent working state
- progress.md — Heartbeat and test progression
