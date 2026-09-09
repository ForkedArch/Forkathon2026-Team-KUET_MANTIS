# Dispatch: Reviewer M2-2 (Dashboard Layout, Auth & Karma Review)

## Objective
Independently review the frontend layout, authentication, and Karma protocol integration:
1. Verify `DashboardLayout.jsx`, `Sidebar.jsx`, and `TopActionBar.jsx`:
   - Left sidebar with KUET branding, navigation tabs (Map View, All Items, Requests, Profile), student profile card with `⚡ 100 Karma` and logout.
   - Top action bar with search, category dropdown, type filter tabs (All, Lending, Beacons), and `+ Add Item` CTA button.
   - Clean light enterprise styling.
2. Verify `Register` in `frontend/src/App.jsx`:
   - Accepts ONLY 3 fields: Name, Email (`@stud.kuet.ac.bd`), Password.
   - Live roll decoder badge displaying Batch, Dept, Roll, and 100 Base Karma.
3. Verify Karma Protocol UI displays across `Profile.jsx`, `Transaction.jsx`, `Requests.jsx`, `ItemCard.jsx`, `AllItems.jsx`.
4. Verify import resolution across all `frontend/src/` files.

## Input Files
- `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/ORIGINAL_REQUEST.md` (Mandatory read)
- `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/PROJECT.md`
- `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/worker_m2/handoff.md`

## Output
Write report to `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/reviewer_m2_2/handoff.md` with explicit verdict: `APPROVE` or `REQUEST_CHANGES`.

## 2026-09-09T22:28:18Z
You are reviewer_m2_2.
Your working directory is: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/reviewer_m2_2
Your dispatch file is: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/reviewer_m2_2/DISPATCH.md
MANDATORY: Read /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/ORIGINAL_REQUEST.md before starting work.
Read /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/PROJECT.md.
Read Worker handoff: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/worker_m2/handoff.md.

Review Milestone 2 Dashboard layout, Auth, and Karma UI:
1. Verify DashboardLayout.jsx, Sidebar.jsx, TopActionBar.jsx (left sidebar with KUET branding, navigation tabs, student Karma card, top bar with search/type/category filters, + Add Item button).
2. Verify Register in App.jsx (strictly 3 fields: Name, Email, Password; live roll decoder badge).
3. Verify Karma UI displays in Profile, Transaction, Requests, AllItems.
4. Verify import resolution across all frontend/src/ files.
5. Report explicit verdict: APPROVE or REQUEST_CHANGES in:
/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/reviewer_m2_2/handoff.md
Send a completion message when done.
