# Dispatch: Forensic Auditor M2 (Frontend Integrity Verification)

## 2026-09-10T04:28:18Z
You are auditor_m2_1.
Your working directory is: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/auditor_m2_1
Your dispatch file is: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/auditor_m2_1/DISPATCH.md
MANDATORY: Read /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/ORIGINAL_REQUEST.md before starting work.
Read /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/PROJECT.md.
Read Worker handoff: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/worker_m2/handoff.md.

Perform forensic integrity verification on Milestone 2 frontend:
1. Static analysis: verify MapLibre GL JS configuration is authentic and not a hardcoded dummy/image.
2. Verify roll decoding and Karma logic are dynamic and real.
3. Check for cheating, fake test mocks, or evasions.
4. Run `python3 Tanvir/verify_campus_map.py`.
5. Report explicit binary verdict: CLEAN or INTEGRITY VIOLATION in:
/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/auditor_m2_1/handoff.md
Send a completion message when done.
