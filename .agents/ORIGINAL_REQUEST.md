# Original User Request

## 2026-09-09T21:39:24Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Full multi-agent team

The "CampusShare KUET" project currently has a diverged structure. A fully functioning MapLibre UI and Python server exist in the `Tanvir/` folder, while a standard React (`frontend/`) and FastAPI (`backend/`) structure exists separately. Your goal is to integrate the `Tanvir/` assets into the standard structure, implement the remaining business logic, apply a specific UI layout, and iterate against an Agent-as-Judge evaluator using a 20-point rubric until a score of at least 18/20 is achieved.

Working directory: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS
Integrity mode: demo

## Reference Material
- Target UI Layout: Implement a clean, modern, light-themed dashboard layout similar to enterprise asset management tools, but simplified for this prototype.

## Requirements

### R1. Architecture Integration & Cleanup
Port the MapLibre map and UI logic from `Tanvir/index.html` into the React `frontend/`. Move the data and endpoints from `Tanvir/app.py` and `Tanvir/kuet_data/` into the FastAPI `backend/`. Delete the `Tanvir/` directory completely once integration is fully working, leaving only standard naming (`frontend/` and `backend/`).

### R2. UI Layout & Design (Dashboard Style)
Refactor the frontend into a dashboard layout with a left sidebar for navigation (e.g., Map View, My Items, Requests, Profile) and a main content area. The main area should feature a top bar with actions (e.g., "Add Item"), a search/filter bar, and clean tables/lists for items. Use hover cards or popovers to show item details and mini-map locations. The color scheme should be light and clean with subtle brand accents. Keep options minimal for the prototype (no unnecessary tabs like calendar or advanced tags).

### R3. Authentication & KUET Roll Decoder
Update the user registration logic in the FastAPI backend and React frontend. It should only accept Full Name, Password, and Email. The Email must end with `@stud.kuet.ac.bd`. The backend must automatically parse and store the Batch, Department, and Roll number from the email prefix (e.g., `siddique52507028@stud.kuet.ac.bd` -> Batch=25, Dept=07, Roll=028) instead of asking the user to type them. 

### R4. KUET Karma Protocol
Replace the generic 5.0 trust score in the backend schemas with the "KUET Karma Rating System." Users start with 100 Base Karma. When a borrow request is completed, successfully lending adds +10 to the owner, and returning on time adds +5 to the borrower. Returning late deducts -30. Implement this logic in the transaction flows and display it in the frontend UI.

### R5. Automated Evaluation Loop
Run a verification agent (acting as the Judge) that evaluates the integrated system against a 20-point Problem Statement Rubric (4 pts for Integration, 4 pts for UI Layout, 4 pts for Auth, 4 pts for Karma Protocol, 4 pts for End-to-End User Experience). Iterate the implementation until the judge awards at least 18/20.

## Acceptance Criteria

### Integration & UI
- [ ] The `Tanvir/` folder no longer exists in the root repository.
- [ ] The React frontend renders a dashboard layout with a left sidebar, top action bar, and the MapLibre map in the main area.
- [ ] Hover cards or popups are used to display item details, avoiding cluttered full-page redirects where possible.

### Authentication
- [ ] Attempting to register with a non-KUET email fails with an appropriate error.
- [ ] Registration automatically infers the correct batch, department, and roll.

### Karma System
- [ ] New users start with 100 Karma.
- [ ] Completing a transaction correctly updates the Karma scores for both borrower and lender according to the rules.

### End-to-End Flow & Evaluation
- [ ] The full flow (Add Item -> View on Map/List -> Request -> Accept -> Handover -> Return) works without errors.
- [ ] The Agent-as-Judge scripts or processes output an evaluation score of 18/20 or higher.
