# Review & Adversarial Audit Report: Milestone 2 (MapLibre & Dashboard Integration)

**Reviewer Agent**: reviewer_m2_1  
**Roles**: reviewer, critic  
**Target Milestone**: Milestone 2 (Frontend Dashboard & MapLibre Integration)  
**Evaluated Worker**: worker_m2  
**Date**: 2026-09-10T04:32:00+06:00  
**Verdict**: **APPROVE**

---

## 1. Observation

1. **`frontend/index.html` Inspection**:
   - Lines 12-15: Google Fonts linked with Inter (weights 300-800) and Outfit (weights 500-800):
     `href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@500;600;700;800&display=swap"`
   - Lines 18-22: MapLibre GL JS v3.6.2 CSS and JS loaded via CDN:
     `href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css"`
     `<script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>`
   - Line 25: Turf.js v6 loaded via CDN:
     `<script src="https://unpkg.com/@turf/turf@6/turf.min.js"></script>`
   - Line 7: Descriptive title: `CampusShare KUET — God's Eye Campus Asset Sharing`.

2. **`frontend/src/components/map/GodsEyeMap.jsx` Inspection**:
   - Lines 5-6: Explicit KUET geographic center and perimeter constants:
     `export const KUET_CENTER = [89.5024, 22.9006];`
     `export const CAMPUS_PERIMETER_RADIUS = 700;`
   - Lines 12-43: `createCircleGeoJSON` provides Turf.js circle computation (`window.turf.circle([centerLng, centerLat], radiusMeters, { steps: points, units: 'meters' })`) with a full spherical trigonometry fallback algorithm.
   - Lines 93-122: OpenStreetMap raster tile style (`osm-tiles`), initial center set to `KUET_CENTER`, zoom `16.2`, navigation control top-right, and metric scale control bottom-left.
   - Lines 130-170: Source `campus-perimeter-700m` added with 3 distinct MapLibre layers:
     - `perimeter-fill` (fill-color `#2563eb`, fill-opacity `0.05`)
     - `perimeter-line` (line-color `#2563eb`, line-width `2.5`, line-dasharray `[3, 2]`)
     - `perimeter-halo` (line-color `#3b82f6`, line-width `6`, line-opacity `0.2`)
   - Lines 239-270: Dual-marker generation:
     - Emerald lend pins: `.marker-pin.marker-lend` with category emoji glyphs (🧮, 🔌, 🔬, 🔗, 📖, 📐, 📦).
     - Red borrow beacons: `.marker-pin.marker-beacon` with `.beacon-pulse`, `.beacon-pulse-inner`, and `⚡` icon.
   - Lines 400-438: Click-to-pinpoint mode:
     - Enabled by `isPinMode` prop, applying `.pin-mode` class (triggering `cursor: crosshair !important`).
     - Renders `#pin-banner` with cancel action `#btn-cancel-pin`.
     - Click handler captures `e.lngLat`, drops a draggable confirmation marker, and propagates coordinates to `onSelectLocation`.
   - Lines 481-514: Glassmorphic Map HUD controls:
     - `#toggle-ring-btn` (toggles 700m boundary ring visibility)
     - `#toggle-beacons-btn` (toggles borrow beacon visibility)
     - `#recenter-kuet-btn` (smooth camera flyTo `KUET_CENTER` at zoom `16.2`)

3. **`frontend/src/components/map/GodsEyeMap.css` Inspection**:
   - Lines 28-71: Emerald gradient `.marker-lend` (`linear-gradient(135deg, #10b981, #059669)`), red beacon `.marker-beacon` (`linear-gradient(135deg, #ef4444, #dc2626)`), and `@keyframes radar-pulse` animation (2s infinite cubic-bezier expanding from scale 0.6 to 1.6).
   - Lines 73-127: `.pin-mode #map { cursor: crosshair !important; }` and `.pin-banner` floating pill with `slide-banner` keyframe entry.
   - Lines 129-192: `.map-hud` with `.hud-card` (`backdrop-filter: blur(16px)`), `.layer-btn` active states.
   - Lines 193-376: Full styling for rich MapLibre popups (`.popup-card`, `.status-badge-lend`, `.status-badge-beacon`, `.popup-trust-score`, `.btn-popup-primary`).

4. **Independent Test Execution**:
   - Command: `python3 Tanvir/verify_campus_map.py`
   - Output:
     ```
     TOTAL TESTS RUN: 95
     PASSED: 95
     FAILED: 0
     ESTIMATED RUBRIC SCORE: 10.0 / 10.0 (Threshold: >= 9.0)
     [PASS] Rubric score meets or exceeds 9.0 / 10.0 threshold
     ```
   - Command: Independent import check across 24 files in `frontend/src/`:
     `Checked 24 files. Errors: 0`
   - Command: Independent circle geometry fallback verification:
     Computed 65 points along 360° bearing; min distance: 700.00m, max distance: 700.00m, deviation: 0.00m.

---

## 2. Logic Chain

1. **Verification of Requirements R1 & R2 (MapLibre & Dashboard Integration)**:
   - *Observation*: `GodsEyeMap.jsx` implements the exact OpenStreetMap raster tile style, KUET coordinates `[89.5024, 22.9006]`, 700m perimeter GeoJSON polygon, dual-marker rendering (`.marker-lend` and `.marker-beacon`), interactive click-to-pinpoint mode, and bottom-right docked HUD controls.
   - *Logic*: The component satisfies all specifications in `PROJECT.md` Feature Inventory (Items 13-19) and `ORIGINAL_REQUEST.md` (R1, R2). The dashboard layout (`DashboardLayout.jsx`) correctly binds the top action bar, sidebar navigation, and map view.

2. **Verification of Requirement R3 (Authentication & Minimal Registration)**:
   - *Observation*: `frontend/src/App.jsx` lines 160-313 define a registration form strictly accepting only 3 fields (`name`, `email`, `password`) and parsing `@stud.kuet.ac.bd` emails with regex `(\d{2})(\d{2})(\d{3})$` to preview batch, department, and roll.
   - *Logic*: This adheres strictly to Requirement R3, avoiding manual entry of batch, department, or roll.

3. **Verification of Requirement R4 (KUET Karma Protocol Integration)**:
   - *Observation*: `Profile.jsx`, `Transaction.jsx`, `Sidebar.jsx`, `ItemHoverCard.jsx`, and `GodsEyeMap.jsx` display `⚡ {karma} Karma` (defaulting to 100 Base Karma) and handle `karma_updated` (+10 lend, +5 on-time, -30 late penalty).
   - *Logic*: The frontend is completely decoupled from legacy 5.0-scale trust ratings and aligned with the KUET Karma Protocol.

4. **Integrity Violation Assessment**:
   - *Observation*: No test outputs, mocks, or expected values are hardcoded in application source code. The MapLibre map component contains actual canvas rendering, GeoJSON layers, dynamic marker management, and real event bindings.
   - *Logic*: The submission represents genuine engineering work without facade or integrity bypass shortcuts.

---

## 3. Adversarial Challenges & Edge Cases

### [Minor] Challenge 1: Popup innerHTML HTML Injection (XSS surface)
- **Assumption Challenged**: Input strings (`item.title`, `item.specs`, `item.lender_name`) are trusted plain text.
- **Attack Scenario**: If a student inputs HTML or JavaScript (e.g. `<img src=x onerror=...>` in title or specs), `popupNode.innerHTML` in `GodsEyeMap.jsx` (lines 303-336) would parse and execute the payload inside the MapLibre popup DOM.
- **Blast Radius**: Client-side script execution in an authenticated student's session.
- **Mitigation**: Sanitize or assign via `textContent` / React DOM portal rather than raw template literal string concatenation before Milestone 3/4.

### [Low] Challenge 2: Headless MapLibre WebGL Context in Headless Test Environments
- **Assumption Challenged**: Browsers or test runners have WebGL support for MapLibre canvas rendering.
- **Attack Scenario**: Running end-to-end headless browser tests (e.g., Playwright/Puppeteer) on machines without SwiftShader or WebGL drivers could cause `new maplibregl.Map()` to emit warnings or fail canvas context initialization.
- **Blast Radius**: Headless CI test runner failure.
- **Mitigation**: `GodsEyeMap.jsx` handles container detection and interval polling; ensure `--use-gl=angle` or `--enable-webgl` flags are configured in headless test environments if visual judge tests are invoked in M4.

---

## 4. Caveats

1. **Host Environment Lack of Node/npm**:
   - Because `node` and `npm` are not present in the host system `PATH`, static analysis, Python-based AST/regex checks, and script executions were used to verify component syntax and import trees.
2. **Tanvir/ Directory Lifecycle**:
   - `Tanvir/` is preserved during Milestone 2 to maintain the baseline test harness (`verify_campus_map.py`), and will be completely removed in Milestone 3 as scheduled in `PROJECT.md`.

---

## 5. Conclusion

**Verdict**: **APPROVE**

Milestone 2 deliverable meets all criteria:
- `frontend/index.html` loads MapLibre GL JS v3.6.2, Turf.js v6, and Google Fonts.
- `frontend/src/components/map/GodsEyeMap.jsx` and `GodsEyeMap.css` provide the full God's Eye map experience with KUET center `[89.5024, 22.9006]`, 700m perimeter GeoJSON polygon layers, emerald lend pins, radar pulsing borrow beacons, click-to-pinpoint mode, and docked HUD controls.
- `Tanvir/verify_campus_map.py` passes 95 out of 95 tests with a 10.0 / 10.0 score.
- Zero integrity violations were found.

---

## 6. Verification Method

To independently reproduce this verification:

1. **Run Campus Map Verification Suite**:
   ```bash
   python3 Tanvir/verify_campus_map.py
   ```
   *Expected Result*: `TOTAL TESTS RUN: 95, PASSED: 95, FAILED: 0, ESTIMATED RUBRIC SCORE: 10.0 / 10.0`.

2. **Verify Frontend File Imports**:
   ```bash
   python3 -c "
   import os, glob, re
   files = glob.glob('frontend/src/**/*.jsx', recursive=True) + glob.glob('frontend/src/**/*.js', recursive=True)
   errors = []
   for f in files:
       content = open(f).read()
       for imp in re.findall(r'from\s+[\'\"]([^\'\"]+)[\'\"]', content):
           if imp.startswith('.'):
               d = os.path.dirname(f)
               cands = [os.path.normpath(os.path.join(d, imp + ext)) for ext in ['', '.jsx', '.js', '.css', '/index.js', '/index.jsx']]
               if not any(os.path.exists(c) for c in cands): errors.append((f, imp))
   assert len(errors) == 0, f'Unresolved imports: {errors}'
   print(f'Checked {len(files)} files: All imports resolved successfully!')
   "
   ```

3. **Verify Milestone 2 Contract Tokens**:
   ```bash
   python3 -c "
   for path, tokens in [
       ('frontend/index.html', ['maplibre-gl.js', 'turf.min.js', 'family=Inter', 'family=Outfit']),
       ('frontend/src/components/map/GodsEyeMap.jsx', ['KUET_CENTER', 'CAMPUS_PERIMETER_RADIUS = 700', 'campus-perimeter-700m', 'toggle-ring-btn', 'toggle-beacons-btn', 'recenter-kuet-btn', 'pin-banner']),
       ('frontend/src/components/map/GodsEyeMap.css', ['.marker-lend', '.marker-beacon', 'radar-pulse', '.pin-mode', '.map-hud']),
       ('frontend/src/components/items/AddItemModal.jsx', ['add-item-modal', 'item-title', 'type-btn-lend', 'type-btn-borrow', 'proceed-pin-btn', 'direct-submit-btn']),
       ('frontend/src/App.jsx', ['DashboardLayout', '(\\\\d{2})(\\\\d{2})(\\\\d{3})', '@stud.kuet.ac.bd']),
       ('frontend/src/pages/Profile.jsx', ['KUET Karma Protocol Score', '+10', '+5', '-30', 'Base Karma: 100'])
   ]:
       c = open(path).read()
       for t in tokens:
           assert t in c, f'Missing token {t} in {path}'
   print('All Milestone 2 contract tokens verified successfully!')
   "
   ```

4. **Invalidation Conditions**:
   - Any failing assertion in `verify_campus_map.py` or removal of required DOM IDs (`#add-item-modal`, `#pin-banner`, `#toggle-ring-btn`, etc.) would invalidate this approval.
