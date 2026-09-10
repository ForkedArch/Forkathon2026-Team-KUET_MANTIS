# Original User Request

## Initial Request — 2026-09-10T19:09:58Z

# Teamwork Project Prompt

> Status: Launched
> Goal: Fix the production login system failure, deduce and align the website purpose, and perform a complete revision.
> Requested team: Standard full team (Frontend, Backend, Database agents)
> Verification strategies: Automated API testing, Agent-as-judge UI verification

Working directory: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS
Integrity mode: benchmark

## Requirements

### R1. Website Purpose Alignment
KUET CampusShare is a student-exclusive sharing economy platform for Khulna University of Engineering & Technology. Students can borrow, lend, request items, chat, and build trust via a Karma System. The platform restricts access to users with official `@stud.kuet.ac.bd` emails and infers department/batch/roll automatically. The revision should fully align the UI, copy, and backend logic with this purpose.

### R2. Fix Production Login System
Diagnose and fix the issue where the login system is not working on the deployed version (Vercel/Render). Investigate potential causes such as CORS issues, database migration errors, missing environment variables, or frontend-backend API route mismatches. Ensure students can successfully register and log in on production.

### R3. Complete Platform Revision
Perform a thorough review and revision of the platform to ensure core features (Item Listing, Item Request, Chat, Profile, Karma System) function seamlessly end-to-end. Fix any broken layouts, unhandled API errors, or missing states. Ensure the Vercel (frontend) and Render (backend) deployments are robust.

## Acceptance Criteria

### Authentication & Security
- [ ] Programmatic: The login and registration API endpoints return successful responses in production environments.
- [ ] Agent-as-judge: An independent agent verifies that a valid KUET email can successfully register and log in, and invalid emails are correctly rejected.

### End-to-End Functionality
- [ ] Programmatic: The frontend application builds successfully and the backend starts without errors.
- [ ] Agent-as-judge: An independent agent verifies that the core flows (borrowing/lending items, sending messages, viewing profiles) are aligned with the platform's purpose and function without errors.

## Follow-up — 2026-09-10T19:36:29Z

The user has provided some urgent feedback regarding the deployment:

"Even after redeploying the UI did not change instead the login and sign up both system stopped working."

The user also uploaded two screenshots:
1. A screenshot of the registration page attempting to register with `siddique2507028@stud.kuet.ac.bd`. A toast notification at the top displays a "Not Found" (404) error. This likely means the frontend is hitting a 404 endpoint for `/api/auth/register`, possibly due to a missing/incorrect `VITE_API_URL` or a `vercel.json` rewrite issue.
2. A screenshot of the deployed homepage showing the map view ("God's Eye Map"). The user noted the "UI did not change" as they expected.

Please incorporate this feedback into your troubleshooting and revision process immediately.

## Follow-up — 2026-09-10T19:43:04Z

The user is concerned about the duration and token cost. Please expedite the process. Focus strictly on fixing the critical 404 API routing issue (`vercel.json`/`VITE_API_URL`) and making the necessary UI alignment changes (removing "God's Eye Map", ensuring KUET branding). Avoid any non-essential refactoring or unnecessary subagent spawning. Finish and claim victory as soon as the core issues are resolved and tested.
