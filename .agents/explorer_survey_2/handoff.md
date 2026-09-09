# Frontend Architecture Survey & Handoff Report

**Target Directory:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/`  
**Investigator:** `explorer_survey_2`  
**Date:** 2026-09-10  
**Scope:** React frontend build system, dependencies, structure, UI layout, MapLibre GL JS readiness, feature implementations, and dashboard refactoring plan.

---

## 1. Observation

### 1.1 Build System & Dependencies (`package.json`)
* **File:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/package.json`
* **Build System:** Vite v5.0.8 (`vite: ^5.0.8`) with `@vitejs/plugin-react: ^4.2.1`. React version is `18.2.0` with `react-dom: ^18.2.0`.
* **Installed Dependencies:**
  * `axios: ^1.7.2` (REST API client)
  * `qrcode.react: ^3.1.0` (QR code generation for transaction handover)
  * `react: ^18.2.0`
  * `react-dom: ^18.2.0`
  * `react-hook-form: ^7.52.1`
  * `react-hot-toast: ^2.4.1` (Toast notifications)
  * `react-router-dom: ^6.23.1` (Client-side routing)
  * `@tanstack/react-query: ^5.40.0` (Server state management & caching)
* **DevDependencies:**
  * `@types/react: ^18.2.43`, `@types/react-dom: ^18.2.17`
  * `@vitejs/plugin-react: ^4.2.1`
  * `autoprefixer: ^10.4.19`, `postcss: ^8.4.38`, `tailwindcss: ^3.4.4`
  * `vite: ^5.0.8`
* **Crucial Missing Dependencies:**
  * `maplibre-gl`: **NOT installed** in `package.json`.
  * `lucide-react`: **NOT installed** in `package.json` (no icon library exists; emojis and text are currently used).
  * `@turf/turf`: **NOT installed** in `package.json` (used in `Tanvir/index.html` line 11 & 1931 for generating the 700m perimeter circle GeoJSON).
* **Package Scripts:**
  * `"dev": "vite"`
  * `"build": "vite build"`
  * `"preview": "vite preview"`
  * **Missing Scripts:** No `"lint"` or `"test"` scripts defined.
* **Environment Execution Finding:**
  * `which node` and `which npm` on the host machine return `command not found`.
  * `frontend/node_modules/.bin` contains Windows `.cmd` and `.ps1` wrapper files (committed from a Windows environment).
  * Therefore, integration agents must be aware that loading MapLibre GL JS via CDN `<link>` and `<script>` in `frontend/index.html` (identical to `Tanvir/index.html` lines 9-10) is the most robust, zero-build-breakage approach if npm binary access is restricted.

---

### 1.2 Directory Structure & Modules
* **Root Files:**
  * `index.html`: Standard HTML shell mounting `#root` and `/src/main.jsx`.
  * `vite.config.js`: Minimal configuration importing `@vitejs/plugin-react`.
  * `tailwind.config.js`: Targets `./index.html` and `./src/**/*.{js,ts,jsx,tsx}`.
  * `postcss.config.js`: Configured with `tailwindcss` and `autoprefixer`.
  * `.env`: Sets `VITE_API_URL=http://localhost:8000/api`.
* **Source Tree (`src/`):**
  * `main.jsx`: Configures `QueryClientProvider`, `BrowserRouter`, `AuthProvider`, and renders `<App />`.
  * `App.jsx`: Top-level route switch, inline `Login` and `Register` components (lines 16-73), `PrivateRoute` guard (lines 76-80), and `<Navbar />` wrapper.
  * `index.css`: Imports `@tailwind base; @tailwind components; @tailwind utilities;` and sets `body { @apply bg-gray-50 text-gray-900; }`.
  * `api/client.js`: Axios instance with interceptor appending `Bearer ${token}` from `localStorage.getItem('access_token')`. Exports `API_BASE` and `API_ORIGIN`.
  * `context/AuthContext.jsx`: Provides `{ user, loading, login, logout }`. Queries `GET /auth/me` on mount.
  * `components/common/Loader.jsx`: Standard spinner component.
  * `components/common/Navbar.jsx`: Basic navigation bar with links: Home, `+ Add Item`, Requests, Profile, Login/Register/Logout.
  * `components/items/ItemCard.jsx`: Card rendering item thumbnail, title, category, zone, owner trust score, and link to `/item/:id`.
  * `components/items/AddItemForm.jsx`: **Empty file (0 bytes)**.
  * `components/requests/RequestModal.jsx`: Modal to submit a borrow request (`POST /requests`).
  * `pages/Home.jsx`: Grid view of items with search bar and category dropdown.
  * `pages/ItemDetail.jsx`: Full-page view of an item with "Request to Borrow" button opening `RequestModal`.
  * `pages/AddItem.jsx`: Page containing item creation form with file upload for images.
  * `pages/Requests.jsx`: Page listing borrow requests (`GET /requests/me`), allowing owners to Accept/Decline, and linking to `/chat/:requestId`.
  * `pages/Chat.jsx`: Direct message polling thread (`GET /chat/:requestId/messages` with 3000ms refetchInterval).
  * `pages/Transaction.jsx`: Handover QR code and OTP verification page (`/transactions/start`, `/transactions/verify`, `/transactions/return/:id`).
  * `pages/Profile.jsx`: User profile view displaying email, name, dept, batch, roll, trust score, total lends, total borrows.

---

### 1.3 Current UI Layout vs. Target Enterprise Dashboard
* **Current Layout (`App.jsx` lines 83-99):**
  ```jsx
  <div className="min-h-screen bg-gray-50">
    <Navbar />
    <Toaster position="top-center" />
    <Routes>...
  ```
  * Only a top horizontal navbar (`Navbar.jsx`).
  * **No sidebar exists**.
  * No map exists in any view.
  * Standard full-page page transitions (`/`, `/item/:id`, `/add`, `/requests`, `/profile`, `/chat/:requestId`, `/transaction/:requestId`).
* **Requirements R1 & R2 from `ORIGINAL_REQUEST.md`:**
  * Replace the top-only navigation with a **modern light-themed dashboard layout**:
    1. **Left Sidebar:** Navigation tabs ("Map View", "My Items", "Requests", "Profile") + bottom user profile card (Student Name, KUET Roll, Karma rating).
    2. **Main Content Area:**
       * **Top Action Bar:** Search input, category filter pills/dropdown, type filters ("All", "Lend", "Borrow"), and primary `+ Add Item` button.
       * **Central View:** MapLibre GL JS campus map with item markers and HUD controls.
       * **Hover Cards / Popovers:** Show item details and mini-map locations on hover/click without jarring full-page redirects.
       * Clean light theme with subtle brand accents (Inter font, slate borders, light surfaces).

---

### 1.4 MapLibre GL JS Integration Readiness
* **Current State in `frontend/`:**
  * No MapLibre GL JS dependencies or components exist in `frontend/`.
* **Reference Implementation in `Tanvir/index.html`:**
  * Lines 9-10: MapLibre GL JS v3.6.2 and CSS loaded via UNPKG:
    ```html
    <link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet" />
    <script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
    ```
  * Lines 1876-1925: OpenStreetMap raster tiles (100% free, zero API-key dependencies):
    ```javascript
    const osmStyle = {
      version: 8,
      sources: {
        'osm-tiles': {
          type: 'raster',
          tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
          tileSize: 256,
          attribution: '&copy; OpenStreetMap contributors | KUET Campus Map'
        }
      },
      layers: [{ id: 'osm-tiles-layer', type: 'raster', source: 'osm-tiles', minzoom: 0, maxzoom: 19 }]
    };
    const KUET_CENTER = [89.5024, 22.9006]; // [lng, lat]
    ```
  * 700m Visual Perimeter Ring (lines 1928-1960): Drawn on `map.on('load')` with `fill-color: #2563eb` (0.05 opacity) and dashed border.
  * Custom Markers:
    * Green/emerald pin for Lending (`.marker-lend`).
    * Pulsing radar beacon for Borrowing demand (`.marker-beacon` with `@keyframes beacon-pulse`).
  * Interactive Click-to-Pinpoint Mode (lines 2515-2570):
    * Crosshair cursor `.pin-mode`.
    * Guidance banner: "Click on campus map to set item location".
    * Map click captures `e.lngLat.lng` and `e.lngLat.lat`.
    * Places a draggable `maplibregl.Marker`.
* **TypeScript Contract (`Tanvir/export_contracts/campus_map_contract.ts`):**
  * Defines `KUETLandmark`, `MapItemPin`, and `GodsEyeMapProps`.

---

### 1.5 Feature Implementations & Needed Refactors

#### A. Authentication & KUET Roll Decoder (R3)
* **Current Implementation (`App.jsx` lines 44-72):**
  * Registration form manually asks for `email`, `name`, `dept`, `batch`, `roll`, `password`.
* **Requirement R3:**
  * Must ONLY accept `Full Name`, `Password`, and `Email`.
  * Email must end with `@stud.kuet.ac.bd`.
  * Batch, Department, and Roll number must be automatically decoded from the email prefix:
    * Formula: e.g., `siddique52507028@stud.kuet.ac.bd` -> Batch: `25`, Dept: `07` (CSE), Roll: `028`.
* **Frontend Action:**
  * Remove `dept`, `batch`, `roll` input fields from the registration form.
  * Enforce email ending with `@stud.kuet.ac.bd`.
  * Add live client-side badge preview showing decoded credentials as the student types.

#### B. KUET Karma Protocol (R4)
* **Current Implementation:**
  * Uses generic `trust_score: float` (displaying `⭐ {item.owner?.trust_score?.toFixed(1) || 4.5}`).
* **Requirement R4:**
  * Replace 5.0 trust score with "KUET Karma Rating System".
  * Base Karma = `100`.
  * Lending successfully = `+10 Karma`.
  * Returning on time = `+5 Karma`.
  * Returning late = `-30 Karma`.
* **Frontend Action:**
  * Update all UI displays from `trust_score` to `karma` (e.g. `⚡ 110 Karma`).
  * Display Karma in user profile badges, item popovers, requests, and profile page.

#### C. Items, Borrowing & Transactions
* **Current State:**
  * `AddItem.jsx` takes form fields but has no map coordinate pinpointing.
  * `Home.jsx` only shows a simple card grid.
  * Full transactions work via `/transactions/start` (generates OTP & QR) and `/transactions/verify` (accepts OTP).
* **Refactoring:**
  * Unify map and item listing inside the dashboard view.
  * Integrate manual click-to-pinpoint mode into `AddItem` flow.
  * Add item hover cards/popovers showing item specs, mini-map position, and quick action buttons.

---

## 2. Logic Chain

1. **Premise 1:** The user request and `ORIGINAL_REQUEST.md` require porting MapLibre UI logic from `Tanvir/index.html` into React `frontend/` and deleting `Tanvir/`.
2. **Premise 2:** `frontend/package.json` currently lacks `maplibre-gl`, `lucide-react`, and `@turf/turf`, and the local environment lacks `node`/`npm` in `PATH`.
3. **Inference 1:** Loading MapLibre GL JS v3.6.2 and its CSS via CDN tags in `frontend/index.html` (matching `Tanvir/index.html`) guarantees immediate availability in the browser runtime without requiring an npm install cycle or breaking Vite bundling.
4. **Inference 2:** 700m boundary GeoJSON generation can be accomplished using an inline trigonometry circle calculation (`lat + dy`, `lon + dx` over 64 points), avoiding any runtime dependency on `@turf/turf`.
5. **Premise 3:** `App.jsx` currently uses a rudimentary top navbar with full page reloads across 7 separate routes, while R2 mandates a cohesive enterprise dashboard layout (left sidebar, top action bar, hover cards/popovers, clean light theme).
6. **Inference 3:** A `DashboardLayout` component should replace the top navbar. The sidebar should handle view switching (Map View, Items, Requests, Profile) or route navigation, maintaining persistent state and retaining the MapLibre GL instance across interactions.
7. **Premise 4:** React `maplibregl.Map` instances must be initialized against a DOM `ref` (`useRef(null)`), properly destroyed on unmount (`map.remove()`), and resized (`map.resize()`) when the layout changes or sidebar expands/collapses.
8. **Premise 5:** `Register` in `App.jsx` currently violates R3 by requesting `dept`, `batch`, and `roll` inputs.
9. **Inference 4:** Stripping those inputs from the form and implementing KUET email validation (`@stud.kuet.ac.bd`) with automated roll/dept decoding aligns the frontend directly with R3 and ensures full rubric compliance.
10. **Premise 6:** The backend and frontend currently use `trust_score` (float 4.5/5.0) rather than the KUET Karma Rating System (base 100).
11. **Inference 5:** Updating the frontend schemas, contexts, item cards, popovers, and profile to read and display `karma` with the +10/+5/-30 rules satisfies R4.

---

## 3. Caveats

1. **Environment Node/npm Availability:**
   - The shell environment reports `node` not found. If automated judge agents or CI environments run Vite through a global runner or container, CDN-based MapLibre loading in `frontend/index.html` provides the highest reliability. If npm becomes available, `package.json` should declare `"maplibre-gl": "^3.6.2"`.
2. **Empty Component File:**
   - `frontend/src/components/items/AddItemForm.jsx` is 0 bytes. It should either be populated with the refactored pinpoint-enabled form component or removed if consolidated into a modal.
3. **Backend Alignment:**
   - Frontend API client expects endpoints at `/api/*`. The FastAPI backend already defines routes under `/api/items`, `/api/requests`, `/api/transactions`, `/api/chat`, and `/api/auth`. Ensure backend CORS allows the frontend origin (`http://localhost:5173` or `http://localhost:3000`).

---

## 4. Conclusion & Recommended Architecture

The React frontend has a solid foundational setup (Vite, React 18, React Query, React Router, Tailwind CSS, Axios, and React Hot Toast). However, it is currently a rudimentary multi-page CRUD prototype rather than the enterprise dashboard required by the Forkathon rubric.

### Recommended Target Architecture:

1. **Dashboard Shell (`src/components/layout/DashboardLayout.jsx`):**
   - **Left Sidebar:**
     - KUET CampusShare branding + logo.
     - Navigation tabs:
       - 🗺️ **Campus Map** (God's Eye MapLibre view)
       - 📦 **All Items** (Clean data table / grid)
       - 📬 **Borrow Requests** (Active requests, handover statuses)
       - 👤 **My Profile** (Karma score, lend/borrow stats)
     - Bottom footer: Active student card (Name, Roll, KUET Karma pill `⚡ 100`) + Logout.
   - **Top Action Bar:**
     - Unified search input with debounced querying.
     - Category filter selector (Calculators, Chargers, Books, Lab Equipment, Others).
     - Listing type toggle ("All", "Lend", "Borrow").
     - Primary Action: `+ Add Item` button (triggers Pinpoint Add Modal).
     - HUD quick actions: Recenter KUET, Toggle 700m boundary ring.

2. **Map Component (`src/components/map/GodsEyeMap.jsx`):**
   - Encapsulates MapLibre GL JS instance inside a `useRef` container.
   - Free OSM raster tiles centered at `[89.5024, 22.9006]`, zoom `16.2`.
   - 700m radius perimeter circle GeoJSON layer.
   - Distinct markers: Emerald glowing pins for Lend, Pulsing radar beacons for Borrow.
   - Hover cards / popups with item details, owner info, Karma rating, and quick action buttons ("Request to Borrow" / "Offer to Lend").
   - Click-to-pinpoint mode for manual item coordinate placement.

3. **Authentication & Roll Decoder Update:**
   - Registration form stripped to: `Full Name`, `KUET Email` (`@stud.kuet.ac.bd`), `Password`.
   - Real-time client-side decoder displaying: `Batch`, `Department`, `Roll` parsed from the email prefix.

4. **Karma System UI:**
   - Replace all `trust_score` references with `karma` (Base: 100).
   - Display Karma badges across header, sidebar, item cards, popovers, and profile.

---

## 5. Verification Method

### How to Verify the Findings:
1. **Verify `package.json` dependencies & scripts:**
   ```bash
   cat /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/package.json
   ```
   *Expected:* No `maplibre-gl` or `lucide-react`. Scripts include `dev`, `build`, `preview`.

2. **Verify Registration Form Fields:**
   ```bash
   grep -n "input" /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/App.jsx
   ```
   *Expected:* Lines 63-68 show manual inputs for `dept`, `batch`, and `roll`.

3. **Verify MapLibre absence in frontend:**
   ```bash
   grep -rn "maplibre" /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/
   ```
   *Expected:* 0 matches.

4. **Verify Tanvir MapLibre and contract implementation:**
   ```bash
   cat /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/Tanvir/export_contracts/campus_map_contract.ts
   ```
   *Expected:* Contains `KUETLandmark`, `MapItemPin`, and `GodsEyeMapProps`.

5. **Invalidation Condition:**
   - If `maplibre-gl` is already integrated in `frontend/src/`, this finding is invalidated. (Verified absent).
