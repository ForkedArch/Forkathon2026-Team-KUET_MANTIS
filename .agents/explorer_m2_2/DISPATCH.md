# Dispatch: Explorer M2-2 (Dashboard Shell Layout & Navigation)

## Objective
Detail the precise React component architecture for the Enterprise Dashboard Layout (R2):
1. `DashboardLayout.jsx`:
   - Left Sidebar:
     - KUET CampusShare branding and logo.
     - Navigation items: Map View (`/`), All Items (`/items`), Borrow Requests (`/requests`), Profile (`/profile`).
     - Bottom student profile card: Student Name, Roll, KUET Karma rating badge (`⚡ 100 Karma`), Logout button.
   - Main Content Area:
     - Top Action Bar: Search input, Category pills/dropdown, Listing type toggle ("All", "Lending", "Beacons"), and primary `+ Add Item` CTA button.
     - Clean, light enterprise theme with subtle accents (slate borders, light background `#f8fafc`).
2. Routing & Integration with `App.jsx`:
   - Wrap application routes in `DashboardLayout`.
   - Maintain MapLibre instance and view switches cleanly.

## Input Files
- `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/ORIGINAL_REQUEST.md` (Mandatory read)
- `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/PROJECT.md`
- `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_survey_2/handoff.md`

## Output
Write findings and exact JSX/CSS code templates to:
`/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_m2_2/handoff.md

## 2026-09-09T22:18:12Z
Detail the Dashboard Shell Layout (R2):
1. Left sidebar (Map, Items, Requests, Profile navigation, KUET branding, active student footer with Karma score).
2. Top action bar (+ Add Item, search bar, category pills, type filters).
3. Clean light enterprise theme.
Write complete code recommendations to:
/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_m2_2/handoff.md
Send a completion message when done.
`
