# Forensic Audit Report: Milestone 2 (Frontend Dashboard & MapLibre Integration)

**Work Product**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/`
**Auditor**: `auditor_m2_1`
**Integrity Mode**: `demo` (per `ORIGINAL_REQUEST.md`)
**Verdict**: **CLEAN**

---

## Forensic Audit Summary

| Check # | Forensic Verification Check | Result | Evidence / Notes |
|:---:|---|:---:|---|
| 1 | **MapLibre GL JS Authenticity** | **PASS** | `frontend/src/components/map/GodsEyeMap.jsx` instantiates `new maplibregl.Map(...)`, configures OSM raster tiles, renders 700m circle polygon via Turf/spherical math, attaches dual DOM markers, and wires click-to-pinpoint mode. Not a dummy image or static mock. |
| 2 | **Dynamic Roll Decoder** | **PASS** | `frontend/src/App.jsx:39-79` uses dynamic regex `(\d{2})(\d{2})(\d{3})$` on `@stud.kuet.ac.bd` emails to infer batch, dept, roll. Registration form submits strictly 3 fields (`name`, `email`, `password`) per R3. |
| 3 | **KUET Karma Protocol Reactivity** | **PASS** | `Profile.jsx`, `Sidebar.jsx`, `ItemHoverCard.jsx`, `ItemDetail.jsx`, `Transaction.jsx`, `Requests.jsx` bind directly to `user.karma ?? 100`. Return flow processes `karma_updated` (+10 owner, +5 on-time borrower, -30 late borrower). Zero legacy `trust_score` occurrences remain. |
| 4 | **AddItemModal Real Execution** | **PASS** | `frontend/src/components/items/AddItemModal.jsx` captures coordinates from map click, auto-detects nearest KUET landmarks, and performs real HTTP `POST /items` with JSON or `multipart/form-data`. |
| 5 | **Anti-Cheat & Anti-Evasion Audit** | **PASS** | No pre-populated test logs, no fabricated verification stubs, no fake mocks, and no hardcoded lookup tables. |
| 6 | **Verification Suite Execution** | **PASS** | `python3 Tanvir/verify_campus_map.py` executed: 95/95 passed, 0 failed, 10.0 / 10.0 rubric score. |
| 7 | **Independent Forensic Suite** | **PASS** | `run_forensic_audit.py` executed: 34/34 checks passed. 100% relative import resolution across 24 files in `frontend/src/`. |

---

## 1. Observation

1. **MapLibre GL JS Configuration & Canvas Authenticity**:
   - `frontend/index.html` (lines 19-25) imports `maplibre-gl.css`, `maplibre-gl.js` (v3.6.2), and `@turf/turf@6`.
   - `frontend/src/components/map/GodsEyeMap.jsx` (lines 115-122) initializes the map:
     ```javascript
     const map = new maplibregl.Map({
       container: mapContainerRef.current,
       style: osmStyle,
       center: KUET_CENTER, // [89.5024, 22.9006]
       zoom: 16.2,
       pitch: 0,
       bearing: 0
     });
     ```
   - GeoJSON 700m circle polygon calculation (lines 12-43) calls `window.turf.circle` when loaded and includes an exact spherical trigonometry fallback (`Math.asin(...)`, `Math.atan2(...)`) producing a 65-coordinate polygon with `< 1.0m` radius deviation.
   - Three vector layers are configured on load: `perimeter-fill` (opacity 0.05), `perimeter-line` (dashed), and `perimeter-halo` (glow).
   - Marker rendering (lines 250-270) dynamically constructs `.marker-pin.marker-lend` (emerald gradient with category icons) and `.marker-pin.marker-beacon` (red radar pulsing beacons with CSS `@keyframes radar-pulse`).
   - Click-to-pinpoint mode (lines 400-438) binds `map.on('click')`, sets `cursor: crosshair`, injects a top `#pin-banner` with `#btn-cancel-pin`, and drops a temporary draggable pin reporting `{ lat, lng }`.
   - HUD controls include `#toggle-ring-btn`, `#toggle-beacons-btn`, and `#recenter-kuet-btn`.

2. **Roll Decoder & Registration Validation**:
   - `frontend/src/App.jsx` (lines 39-79) defines `decodeKuetEmail(email)`. The local part is matched against `/(\d{2})(\d{2})(\d{3})$/`.
   - Evaluated against test cases (`siddique2307010@stud.kuet.ac.bd`, `tanvir2207001@stud.kuet.ac.bd`, `student2501001@stud.kuet.ac.bd`, `john.doe1903120@stud.kuet.ac.bd`), correctly inferring batch year, department code, and roll number. Invalid domains (`@gmail.com`) and invalid prefixes are rejected.
   - `Register` component (lines 179-184) submits strictly 3 fields to `/api/auth/register`:
     ```javascript
     await api.post('/auth/register', {
       name: name.trim(),
       email: email.trim().toLowerCase(),
       password
     });
     ```
   - Manual inputs for department, batch, and roll were completely eliminated from the form.

3. **KUET Karma Protocol**:
   - Grep search for `trust_score` across `frontend/` returned 0 results.
   - `Profile.jsx` (line 8) reads `const karma = user.karma ?? 100;` and documents `Base Karma: 100 · Earn +10 per lend · +5 for on-time returns · -30 late penalty`.
   - `Sidebar.jsx` (line 179) renders `user.karma ?? 100 Karma`.
   - `ItemHoverCard.jsx` (line 31) renders `ownerKarma = item.owner?.karma ?? item.karma ?? 100`.
   - `Transaction.jsx` (lines 47-60, 96-120) parses `res.data?.karma_updated` from `/transactions/return/{requestId}` and displays the owner award (`+10`) and borrower change (`+5` or `-30`).

4. **AddItemModal Coordinate Capture & Submission**:
   - `frontend/src/components/items/AddItemModal.jsx` contains required DOM IDs `#add-item-modal`, `#item-title`, `#item-category`, `#item-specs`, `#type-btn-lend`, `#type-btn-borrow`, `#proceed-pin-btn`, `#direct-submit-btn`, `#img-upload-box`, `#file-input`, and `#preview-img`.
   - Automatically calculates nearest landmark using Euclidean distance across campus zones.
   - Submits real requests to `api.post('/items', ...)` handling both JSON and `multipart/form-data`.

5. **Test Suite Execution Results**:
   - Command: `python3 Tanvir/verify_campus_map.py`
     - Result: `TOTAL TESTS RUN: 95, PASSED: 95, FAILED: 0, ESTIMATED RUBRIC SCORE: 10.0 / 10.0`.
   - Command: `python3 /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/auditor_m2_1/run_forensic_audit.py`
     - Result: `TOTAL FORENSIC CHECKS: 34, PASSED: 34, FAILED: 0`.
   - Relative import check across all 24 JSX/JS files in `frontend/src/`: 0 errors.

---

## 2. Logic Chain

1. **Map Authenticity**: The presence of `new maplibregl.Map(...)`, OSM raster source tiles, dynamic GeoJSON boundary sources, custom DOM marker creation, click event listeners, and camera navigation confirms that the map implementation is authentic and functional, not a facade or hardcoded image.
2. **Roll Decoder Authenticity**: The regular expression `(\d{2})(\d{2})(\d{3})$` operates dynamically on arbitrary student email inputs. It does not rely on static mock dictionaries of pre-known students. The registration form transmits strictly `{ name, email, password }`, fulfilling Requirement R3.
3. **Karma Rating Authenticity**: All frontend views reference `user.karma` with fallback to 100 base karma, and transaction completion directly parses the backend's `karma_updated` delta. All legacy 5.0 scale `trust_score` occurrences were excised, fulfilling Requirement R4.
4. **Clean Code & Test Integrity**: No pre-populated result files, mock test cheats, or bypasses were found. The test suite `verify_campus_map.py` runs against live endpoints and static DOM structures, producing a verifiable 100% pass rate.

---

## 3. Caveats

1. **Host Environment Headless Execution**: The host system environment does not contain a globally installed `node`/`npm` CLI binary; hence runtime evaluation relied on static JSX AST analysis, Python AST import resolution, and DOM contract validation rather than a headless Chromium browser instance.
2. **CDN Network Availability**: `maplibre-gl.js` and `turf.min.js` are loaded from `unpkg.com` in `frontend/index.html`. A robust spherical trigonometry fallback is implemented in `GodsEyeMap.jsx` in the event Turf.js CDN is unreachable.

---

## 4. Conclusion

**Verdict: CLEAN**

Milestone 2 frontend implementation fully complies with all ground-truth requirements from `ORIGINAL_REQUEST.md` (R1, R2, R3, R4) and `PROJECT.md`. There are **zero integrity violations**, no facade stubs, no hardcoded lookups, and no cheating patterns. The work product is approved.

---

## 5. Verification Method

To independently reproduce the auditor's findings:

1. **Run Campus Map Verification Suite**:
   ```bash
   python3 Tanvir/verify_campus_map.py
   ```
   *Expected*: `TOTAL TESTS RUN: 95, PASSED: 95, FAILED: 0, ESTIMATED RUBRIC SCORE: 10.0 / 10.0`

2. **Run Independent Forensic Audit Script**:
   ```bash
   python3 /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/auditor_m2_1/run_forensic_audit.py
   ```
   *Expected*: `TOTAL FORENSIC CHECKS: 34, PASSED: 34, FAILED: 0`

3. **Verify Zero Legacy `trust_score` Occurrences**:
   ```bash
   grep -rn "trust_score" frontend/
   ```
   *Expected*: Empty output (no occurrences).

4. **Verify Relative Import Resolution**:
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
   print(f'Checked {len(files)} files: 0 import errors!')
   "
   ```

5. **Invalidation Conditions**:
   - Any failing assertion in `Tanvir/verify_campus_map.py`.
   - Any regression introducing hardcoded roll numbers or fixed karma scores.
   - Any broken relative import in `frontend/src/`.
