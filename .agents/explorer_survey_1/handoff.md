# Handoff Report: Survey of Tanvir/ Prototype & Porting Architecture

**Agent:** explorer_survey_1  
**Timestamp:** 2026-09-10T03:43:30Z  
**Task:** Complete Survey & Technical Documentation of `Tanvir/` assets and migration path into `frontend/` & `backend/`.

---

## 1. Observation

Direct examination of the repository files, code lines, schemas, contracts, and test executions revealed the following factual structure:

### 1.1 Directory Structure of `Tanvir/`
The `Tanvir/` directory contains:
- `Tanvir/index.html` (2,692 lines, 90,602 bytes): Standalone frontend delivering MapLibre GL JS map, live sidebar feed, filter system, interactive pinpointing, and modal dialogs.
- `Tanvir/app.py` (246 lines, 9,498 bytes): Threaded zero-dependency Python HTTP server and REST API.
- `Tanvir/kuet_data/kuet_landmarks.json` (439 lines, 15,523 bytes): Canonical campus geographic data, landmark definitions, and mock items.
- `Tanvir/export_contracts/campus_map_contract.ts` (46 lines, 1,292 bytes): TypeScript interface definitions for integrating the map component (`GodsEyeMapProps`, `KUETLandmark`, `MapItemPin`, `LandmarkCategory`).
- `Tanvir/verify_campus_map.py` (435 lines, 21,876 bytes): Self-contained test suite executing 95 automated assertions verifying map geometry, radius, API endpoints, mock data, DOM structures, and pinpoint workflows. Execution result:
  `TOTAL TESTS RUN: 95 | PASSED: 95 | FAILED: 0 | ESTIMATED RUBRIC SCORE: 10.0 / 10.0`.
- `Tanvir/README.md` (57 lines): Prototype documentation outlining features and execution instructions (`python3 app.py 8000`).

### 1.2 Detailed Breakdown of `Tanvir/index.html`
- **Dependencies (CDNs)**:
  - MapLibre GL JS v3.6.2: `<link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet" />`, `<script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>` (lines 9-10).
  - Turf.js v6: `<script src="https://unpkg.com/@turf/turf@6/turf.min.js"></script>` (line 11).
  - Google Fonts: Inter (300, 400, 500, 600, 700) and Outfit (500, 600, 700, 800) (lines 14-16).
- **MapLibre GL Configuration**:
  - Center: `KUET_CENTER = [89.5024, 22.9006]` `[lng, lat]` (line 1465).
  - Zoom: `16.2`, Pitch: `0`, Bearing: `0` (lines 1906-1908).
  - Tile Source: OpenStreetMap raster tiles `https://tile.openstreetmap.org/{z}/{x}/{y}.png`, `tileSize: 256`, attribution to OpenStreetMap contributors (lines 1880-1889).
  - Controls: `maplibregl.NavigationControl({ visualizePitch: true })` docked `top-right`, `maplibregl.ScaleControl({ unit: 'metric' })` docked `bottom-left` (lines 1912-1913).
  - Perimeter Ring (700m Radius): Function `drawPerimeterCircle(700)` computes polygon with `turf.circle(KUET_CENTER, 700, { steps: 64, units: 'meters' })` (lines 1928-1970). Three layers rendered:
    1. `perimeter-fill` (`fill-color: #2563eb`, `fill-opacity: 0.05`).
    2. `perimeter-line` (`line-color: #2563eb`, `line-width: 2.5`, `line-dasharray: [3, 2]`).
    3. `perimeter-halo` (`line-color: #3b82f6`, `line-width: 6`, `line-opacity: 0.2`).
- **Markers & Visual Styles**:
  - Clean Map Philosophy: Landmark pins are eliminated on initial load (`landmarkMarkers.forEach(m => m.remove())`, lines 2019-2025) because OpenStreetMap cartographic tiles already label campus buildings clearly without clutter.
  - Item Markers:
    * `marker-lend`: Emerald gradient (`linear-gradient(135deg, #10b981, #059669)`), 32x32px circular pin with white border (`2.5px solid #ffffff`), category-specific emojis (🧮, 🔌, 🔬, 🔗, 📖, 📐, 📦).
    * `marker-beacon`: Red gradient (`linear-gradient(135deg, #ef4444, #dc2626)`), lightning emoji ⚡, dual pulsing radar wave rings (`.beacon-pulse` and `.beacon-pulse-inner` with `@keyframes radar-pulse` expanding from scale 0.6 opacity 1.0 to scale 1.6 opacity 0).
  - Temporary Pin Marker: Rendered with draggable marker during pinpointing (`temporaryPinMarker = new maplibregl.Marker({ draggable: true })`), fires `dragend` to update lat/lng coordinates (lines 2542-2550).
- **Popup Templates**:
  - Encapsulated in `.popup-card` (max width 340px, rounded corners `--radius-lg` 16px).
  - Image banner (140px height) with fallback Unsplash URLs.
  - Status badge: `status-badge-lend` ("🟢 Available to Borrow") or `status-badge-beacon` ("🚨 Active Demand Beacon" with animated pulsing dot).
  - Upper meta: Uppercase category name and condition pill (`Like New`, `Good`, `Fair`).
  - Title and specifications preview box.
  - User detail section: Avatar initials, lender name, department & student badge ('Verified Student', 'KUET Top Lender', etc.).
  - Trust rating box: `⭐ ${trust_rating}/5` and total exchange count.
  - Interactive action buttons: "🤝 Request to Borrow" or "⚡ Offer to Lend This Item" (triggers `handleItemAction`), plus "💬 Chat" button (triggers `handleChatWithUser`).
- **UI Interaction & Event Handlers**:
  - Header: Active student identity badge (`header-user-profile`) showing student name, avatar, dept/batch, roll, and karma (lines 1229-1242, 1561-1587). Radius pill indicator ("📍 700m Campus Perimeter"). "+ Add Item or Request" CTA button.
  - Left Sidebar Feed: Search input (`#search-input`) with real-time filtering; Segmented type tabs (`All Items`, `🟢 Lending`, `🚨 Beacons`); Full-width category dropdown (`#filter-category`); Dynamic results counter; List of `.item-card` elements with hover state and click handler executing `map.flyTo` (zoom 17.5, pitch 35) and toggling popup (lines 2130-2186).
  - Empty State Card: `.empty-state-card` with "🔄 Reset Filters" action calling `window.resetFilters()` (lines 2096-2128).
  - Floating Map HUD: Docked at bottom-right (`.map-hud`), allows toggling 700m perimeter ring visibility, toggling demand beacons visibility, and recentering map to KUET (`KUET_CENTER`).
  - Add Item Modal & Pinpoint Workflow:
    * Modal `#add-item-modal` contains: Listing type switcher (Lend vs Borrow; hides condition on borrow), drag-and-drop/file photo upload with instant FileReader preview, title, category, condition, read-only session user fields, specs/notes, and location status box.
    * "Select Location on Map" (`#proceed-pin-btn`) validates title, stores `pendingFormData`, closes modal, switches body to `.pin-mode` (cursor: crosshair, instruction banner `#pin-banner` displayed).
    * Map click listener (`handleMapClick`) captures exact `e.lngLat`, drops draggable marker, exits pin mode, and invokes `finalizeItemCreation`.
    * `finalizeItemCreation` sends POST to `/api/items`, prepends item to local array, re-renders sidebar & map markers without page reload, flies camera to coordinate, and triggers toast notification (`#toast-container`).

### 1.3 Detailed Breakdown of `Tanvir/app.py`
- Zero external dependencies: Uses Python standard library (`http.server`, `socketserver`, `json`, `urllib.parse`).
- Architecture: `ThreadedHTTPServer(ThreadingMixIn, HTTPServer)` running on port 8000 by default.
- Data Initialization (`init_data`):
  - Reads `kuet_data/kuet_landmarks.json`.
  - Sets `CAMPUS_METADATA = data["campus"]` and `CAMPUS_ZONES = data["zones"]`.
  - Normalizes `sample_active_items`, auto-injecting student credentials:
    `dept_rolls = {"CSE": "2207", "EEE": "2103", "ME": "2005", "Civil": "2201", "ECE": "2205", "BME": "2315"}`
    `user_id`: `student_kuet_<batch>_<idx+1:03d>`
    `roll`: `<roll_prefix><idx+10:03d>`
    `karma`: float trust rating (default 4.8)
- Endpoints Served:
  1. `GET /` & `GET /index.html` -> Serves `index.html` as `text/html; charset=utf-8`.
  2. `GET /api/landmarks` -> Returns `{"success": true, "campus": CAMPUS_METADATA, "zones": CAMPUS_ZONES}`.
  3. `GET /api/items` -> Accepts query parameters:
     - `category`: string filter (case-insensitive, "ALL" ignores)
     - `type`: string filter ("lend", "borrow", "ALL")
     - `q`: search keyword against `title`, `specs`, `lender_name`, `dept`
     Returns `{"success": true, "count": len(filtered), "items": filtered}`.
  4. `GET /api/auth/current` -> Returns demo authenticated student profile (`Tanvir Rahman`, `CSE`, `2022`, roll `2207001`, karma `4.9`, trust_rating `4.9`, badge `Verified Student`, avatar `TR`).
  5. `GET /kuet_data/<path>` -> Serves raw static files from `kuet_data/`.
  6. `POST /api/items` -> Reads JSON body, assigns unique ID `item_<len+101>`, assigns status (`beacon` if type==borrow else `available`), injects student credentials, appends to `LIVE_ITEMS`, returns status `201 Created` with `{"success": true, "item": new_item}`.
  7. `OPTIONS *` -> Returns status `204 No Content` with CORS headers (`Access-Control-Allow-Origin: *`, `Methods: GET, POST, OPTIONS`).

### 1.4 Detailed Breakdown of `Tanvir/kuet_data/`
- **Campus Definition**:
  - Name: "Khulna University of Engineering & Technology (KUET)"
  - Center: `[22.9006, 89.5024]` (Lat 22.9006° N, Lng 89.5024° E)
  - Boundary radius: `700` meters
  - Default zoom: `16.5`
- **21 Landmarks (Campus Zones)**:
  - 4 Academic complexes: CSE Building (`cse_bldg`), EEE Building (`eee_bldg`), Mechanical Building (`me_bldg`), Civil Engineering Building (`civil_bldg`).
  - 7 Residential Halls: Amar Ekushey Hall (`ekushey_hall`), Fazlul Haque Hall (`fazlul_haque_hall`), Lalan Shah Hall (`lalan_shah_hall`), Khan Jahan Ali Hall (`khan_jahan_ali_hall`), Dr. M. A. Rashid Hall (`rashid_hall`), Rokeya Hall (`rokeya_hall`), Bangabandhu Sheikh Mujibur Rahman Hall (`bangabandhu_hall`).
  - Campus Facilities & Hubs: Central Library (`central_library`), Student Cafeteria (`central_cafeteria`), KUET Auditorium (`auditorium`), Administrative Building (`admin_bldg`), Medical Center & Gymnasium (`medical_gym`).
  - Gates & External Perimeter (<700m): KUET Main Entry Gate (`main_gate`), KUET South 2nd Gate (`second_gate`), Fulbarigate Commercial Junction (`fulbarigate_junction`), Teligati Student Mess Zone (`teligati_mess_zone`), Engineering Stationary Hub (`tech_stationary_corner`).
  - All 21 zones have explicit `coords: [lat, lng]` strictly verified by haversine distance to lie within 700m radius of center.
- **10 Sample Active Items**:
  - 7 Lending offers: Casio fx-991CW ClassWiz, Baseus 65W GaN Fast Charger, Arduino Mega 2560 kit, UGREEN 4K 60Hz HDMI Adapter, Rotring Mini Drafter, Heavy Cotton Lab Coat, Higher Engineering Mathematics (B.S. Grewal).
  - 3 Demand Beacons: MacBook MagSafe 3 Cable (urgent 2 hours), Casio fx-991EX for Calculus Term Final, Digital Multimeter with Probes.
  - 8 realistic student profiles with department designations (CSE, EEE, ME, Civil, ECE, BME), batches (2021, 2022, 2023, 2024), trust ratings (4.7 to 4.95), exchange counts (12 to 52), and student badges.

### 1.5 Analysis of Existing `frontend/` and `backend/`
- **Existing `backend/`**:
  - Framework: FastAPI 0.115.6, SQLAlchemy 2.0.36, SQLite database (`campus_share.db`).
  - Models (`backend/app/models.py`):
    * `User`: Has `email`, `name`, `dept`, `batch`, `roll`, `hashed_password`, `trust_score = Column(Float, default=4.5)`. Note: Lacks KUET Karma base 100 model.
    * `Item`: Has `title`, `category`, `description`, `condition`, `image_url`, `latitude`, `longitude`, `zone`, `is_available`, `owner_id`. Note: Lacks `type` ("lend" vs "borrow"), `specs`, `tags`.
    * `BorrowRequest`, `Transaction`, `Message`.
  - Routes (`backend/app/routes/`): `auth.py`, `items.py`, `borrow_requests.py`, `chat.py`, `transactions.py`.
  - Note: No `landmarks.py` exists yet in backend routes.
- **Existing `frontend/`**:
  - Tooling: Vite 5.0.8, React 18.2.0, Tailwind CSS 3.4.4, React Router DOM 6.23.1, @tanstack/react-query 5.40.0, react-hot-toast 2.4.1.
  - Current UI (`frontend/src/pages/Home.jsx`): Basic 4-column grid of `ItemCard` without map integration or sidebar dashboard.
  - Note: `maplibre-gl` and `@turf/turf` are not installed in `frontend/package.json`.
  - Current Registration (`frontend/src/App.jsx` lines 44-73 & `backend/app/routes/auth.py`): Requires users to manually enter `dept`, `batch`, `roll` instead of parsing from `@stud.kuet.ac.bd` email prefix.

---

## 2. Logic Chain

From the observations above, the integration steps and technical decisions logically follow:

1. **Map Engine Porting (`Tanvir/index.html` → `frontend/src/components/map/CampusMap.jsx`)**:
   - *Observation*: `index.html` relies on MapLibre GL 3.6.2 and Turf.js v6 with OSM native raster tiles.
   - *Logic Step 1*: Install `maplibre-gl` in `frontend/package.json`. Turf circle calculation can be handled either via `@turf/turf` (or `@turf/circle`) or clean native trigonometry generating GeoJSON coordinates for the 700m radius circle around `[89.5024, 22.9006]`.
   - *Logic Step 2*: Encapsulate the MapLibre map lifecycle inside a React component (`CampusMap.jsx`) using `useRef` for the map container and `useEffect` for map initialization, layer setup (`perimeter-fill`, `perimeter-line`, `perimeter-halo`), item marker rendering with custom HTML elements (`marker-lend` and `marker-beacon` with `@keyframes radar-pulse`), and popup binding.
   - *Logic Step 3*: Expose props following `Tanvir/export_contracts/campus_map_contract.ts`: `items`, `onSelectLocation`, `isPinMode`, `onSelectItem`.

2. **Dashboard UI Refactoring (`Tanvir/index.html` → `frontend/src/`)**:
   - *Observation*: `ORIGINAL_REQUEST.md` R2 specifies: "Refactor the frontend into a dashboard layout with a left sidebar for navigation (e.g., Map View, My Items, Requests, Profile) and a main content area. The main area should feature a top bar with actions (e.g., 'Add Item'), a search/filter bar, and clean tables/lists for items. Use hover cards or popovers to show item details and mini-map locations."
   - *Logic Step 1*: Create a dedicated `DashboardLayout.jsx` with a fixed Left Sidebar containing navigation links (Map View, My Items, Requests, Profile), user karma badge, and brand logo.
   - *Logic Step 2*: Create a consolidated Main View with Top Bar containing "+ Add Item", Search Input, and Type Tabs (`All`, `🟢 Lending`, `🚨 Beacons`), alongside a view switcher or split layout displaying the MapLibre map and interactive item feed/table.
   - *Logic Step 3*: Port the modal dialog into `AddItemModal.jsx` supporting Listing Type toggle (Lend/Borrow), photo preview, title, category, condition, and the 100% manual click-to-pin coordinate picker mode.

3. **Backend Landmark Data & Route Migration (`Tanvir/kuet_data/` & `Tanvir/app.py` → `backend/app/`)**:
   - *Observation*: `Tanvir/kuet_data/kuet_landmarks.json` holds the authoritative 21 campus zones and 700m radius metadata. `Tanvir/app.py` exposes `GET /api/landmarks`.
   - *Logic Step 1*: Move `kuet_landmarks.json` to `backend/app/data/kuet_landmarks.json`.
   - *Logic Step 2*: Implement `backend/app/routes/landmarks.py` providing `GET /api/landmarks` returning `campus` and `zones` matching Tanvir's contract. Mount it in `backend/app/main.py`.
   - *Logic Step 3*: Seed database items from `sample_active_items` so the FastAPI backend serves the initial KUET campus items.

4. **Authentication & Roll Decoder (R3)**:
   - *Observation*: `ORIGINAL_REQUEST.md` R3 requires accepting only Full Name, Password, and Email ending with `@stud.kuet.ac.bd`. The backend must automatically parse Batch, Dept, and Roll from email prefix (e.g., `siddique52507028@stud.kuet.ac.bd` -> Batch=25, Dept=07, Roll=028).
   - *Logic Step 1*: In `backend/app/schemas.py`, change `UserCreate` to accept only `name`, `email`, `password`.
   - *Logic Step 2*: In `backend/app/routes/auth.py`, enforce `@stud.kuet.ac.bd` domain. Extract roll string (e.g. `2507028` from prefix `siddique52507028`). Parse:
     - `batch = roll_str[0:2]` (e.g. `25`)
     - `dept = roll_str[2:4]` (e.g. `07`, mapped to department name or code)
     - `roll = roll_str[4:]` (e.g. `028` or full roll `2507028`)
   - *Logic Step 3*: Update frontend register form to only ask for Name, Email, Password.

5. **KUET Karma Rating System (R4)**:
   - *Observation*: R4 mandates: Users start with 100 Base Karma. When a borrow request is completed: successfully lending adds +10 to owner, returning on time adds +5 to borrower, returning late deducts -30.
   - *Logic Step 1*: In `backend/app/models.py`, replace `trust_score = Column(Float, default=4.5)` with `karma = Column(Integer, default=100)`.
   - *Logic Step 2*: In `backend/app/routes/transactions.py` (`/return/{request_id}`):
     - Calculate whether return is on time (`trans.returned_at <= due_date` or duration based).
     - Add +10 to owner (`owner.karma += 10`).
     - If on time: add +5 to borrower (`borrower.karma += 5`).
     - If late: deduct -30 from borrower (`borrower.karma -= 30`).
   - *Logic Step 3*: Update Pydantic schemas and frontend user badges to display Karma score.

6. **Tanvir/ Folder Cleanup (R1)**:
   - *Observation*: Acceptance criteria mandates: "The `Tanvir/` folder no longer exists in the root repository."
   - *Logic Step*: Once all components and tests pass against `frontend/` and `backend/`, `rm -rf Tanvir/`.

---

## 3. Caveats

1. **OpenStreetMap Tile Network Access**:
   - `Tanvir/index.html` uses `https://tile.openstreetmap.org/{z}/{x}/{y}.png`. In an offline environment, tile requests return 404 or network timeout, but MapLibre GL JS gracefully falls back to empty background while rendering the GeoJSON perimeter ring, pins, and controls.
2. **Karma Schema Migration**:
   - Existing SQLite database `backend/campus_share.db` contains tables with the previous `trust_score` column. The database must be re-initialized or migrated so that `karma` (default 100) is present and the table schemas reflect the updated requirements.
3. **Roll Decoder Variations**:
   - KUET student roll numbers traditionally take the format `<batch 2 digits><dept 2 digits><roll 3 digits>` (e.g. `2207001` or `2507028`). Some email prefixes contain user letters before digits (e.g. `siddique52507028`). The regex parser must extract the 7 trailing digits before `@stud.kuet.ac.bd` to handle any leading name prefix reliably.

---

## 4. Conclusion

The `Tanvir/` folder delivers a completely functional, highly polished location engine and item log system for KUET:
1. **Accurate MapLibre GL JS 700m Radius Canvas**: Perfectly centered at `[89.5024, 22.9006]` with Turf.js perimeter boundary geometry, native OSM tile integration, and clean map rendering without conflicting landmark markers.
2. **Dual-Marker Visuals**: Distinct emerald pins for offers to lend and animated radar pulsing beacons for demand requests.
3. **Interactive 100% Click-to-Pin Workflow**: Allows users to drop pins anywhere on campus with live coordinates, drag-and-drop image preview, and instantaneous feed updates without page reloads.
4. **Complete Landmark Dataset**: 21 verified KUET landmarks (academic buildings, all 7 residential halls, cafeteria, library, gates) and 10 active student items.
5. **Clear Porting Path**:
   - **Frontend**: Extract map, HUD, and pinpointing into React components under `frontend/src/components/map/` and `frontend/src/components/items/`, adopting the modern light-themed dashboard layout.
   - **Backend**: Move `kuet_landmarks.json` into `backend/app/data/`, expose `GET /api/landmarks`, extend items endpoints with lat/lng and listing type, implement the KUET email decoder (R3), and enforce the 100 Base Karma rating system (R4).
   - **Cleanup**: Delete `Tanvir/` once verification is successful.

---

## 5. Verification Method

To independently verify the survey observations and subsequent migration:

1. **Verify Tanvir Test Suite (Current State)**:
   ```bash
   python3 /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/Tanvir/verify_campus_map.py
   ```
   *Expected Result*: All 95 tests pass with a score of 10.0/10.0.

2. **Verify Static Server & REST Endpoints**:
   ```bash
   python3 -c '
   import json, urllib.request
   import app
   # Check data file integrity
   with open("Tanvir/kuet_data/kuet_landmarks.json") as f:
       data = json.load(f)
   assert len(data["zones"]) == 21, f"Expected 21 zones, got {len(data[\"zones\"])}"
   assert data["campus"]["boundary_radius_meters"] == 700
   print("Landmarks data verified: 21 zones, 700m radius.")
   '
   ```

3. **Verify Frontend Build & Dependencies (Post-Porting)**:
   - Check `frontend/package.json` contains `maplibre-gl`.
   - Run `npm run build` inside `frontend/` to confirm zero compilation errors.

4. **Verify Backend Karma & Email Decoder (Post-Porting)**:
   - Run `pytest` or Python test scripts against `backend/` testing:
     * Registration with `siddique52507028@stud.kuet.ac.bd` yielding `batch="25"`, `dept="07"`, `roll="028"` (or `2507028`).
     * Registration with non-KUET email (e.g. `user@gmail.com`) rejecting with HTTP 400.
     * New user starting with `karma=100`.
     * Transaction completion applying `+10` to lender, `+5` to on-time borrower, `-30` to late borrower.
