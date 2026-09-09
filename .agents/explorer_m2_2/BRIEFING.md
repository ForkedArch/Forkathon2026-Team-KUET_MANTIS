# BRIEFING — 2026-09-10T04:18:30+06:00

## Mission
Investigate and design complete, production-ready code recommendations for Dashboard Shell Layout (R2): Left sidebar, Top action bar, and Clean Light Enterprise theme.

## 🔒 My Identity
- Archetype: explorer
- Roles: explorer, investigator
- Working directory: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_m2_2
- Original parent: e2f4ecb5-c7a3-43bc-9a0e-1232d8641049
- Milestone: Milestone 2 (R2 - Dashboard Shell Layout & Navigation)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement in project src directly; provide complete code recommendations in handoff.md
- Detail Left sidebar (Map, Items, Requests, Profile navigation, KUET branding, active student footer with Karma score)
- Detail Top action bar (+ Add Item, search bar, category pills, type filters)
- Clean light enterprise theme
- Write complete code recommendations to handoff.md and notify caller with send_message

## Current Parent
- Conversation ID: e2f4ecb5-c7a3-43bc-9a0e-1232d8641049
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `ORIGINAL_REQUEST.md` & `PROJECT.md`
  - `.agents/explorer_survey_2/handoff.md`
  - `frontend/package.json` (Vite, React 18, React Router v6, React Query, Tailwind CSS)
  - `frontend/src/App.jsx` (current routes, inline auth)
  - `frontend/src/components/common/Navbar.jsx`
  - `frontend/src/context/AuthContext.jsx`
  - `frontend/src/pages/Home.jsx`, `AddItem.jsx`, `Requests.jsx`, `Profile.jsx`
  - `backend/app/routes/items.py` (query filters for search, category, type)
  - `backend/app/routes/auth.py` & `schemas.py` (UserOut with karma=100, roll decoder)
  - `Tanvir/index.html` (visual references, colors, badges)
- **Key findings**:
  - No `lucide-react` is installed; all icons should be inline SVGs for zero dependency failure risk.
  - `DashboardLayout` cleanly encapsulates `Sidebar` and `TopActionBar` with `<Outlet context={{ ... }} />` and custom hook `useDashboard()`.
  - Left sidebar includes KUET branding, 700m perimeter badge, NavLinks (`/`, `/items`, `/requests`, `/profile`), and active student profile card with `⚡ 100 Karma` rating badge.
  - Top action bar includes search, segmented toggle (All, Lending, Beacons), category selector, and primary `+ Add Item` CTA button.
  - Enterprise light theme configured with Inter typography, slate-50 background, slate-200 borders, and brand accents.
- **Unexplored areas**: None for M2-2 scope.

## Key Decisions Made
- Used zero-dependency inline SVGs for all icons.
- Built `DashboardLayout.jsx` with `<Outlet context={{ ... }} />` to share search, category, and listingType filters between Map View (`/`) and All Items (`/items`).
- Detailed complete, drop-in replacement code files for `DashboardLayout.jsx`, `Sidebar.jsx`, `TopActionBar.jsx`, `AllItems.jsx`, `App.jsx`, and `index.css`.

## Artifact Index
- /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_m2_2/handoff.md — Final 5-component handoff report with complete code recommendations
