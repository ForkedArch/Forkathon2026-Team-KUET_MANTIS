# Review Handoff Report: Milestone 2 Dashboard Layout, Auth & Karma UI

**Reviewer:** reviewer_m2_2  
**Role:** reviewer, critic  
**Timestamp:** 2026-09-10T04:32:00Z  
**Verdict:** **APPROVE**  

---

## 1. Observation

Direct code and test observations from `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS`:

1. **Dashboard Layout Components**:
   - `frontend/src/components/layout/DashboardLayout.jsx`:
     - Line 136-177: Coordinates shell containing `<Sidebar>`, `<TopActionBar>`, `<Outlet context={dashboardValue} />`, and overlays `<AddItemModal>` and `<RequestModal>`.
     - Line 13-19: Exports `useDashboard` hook providing coordinated filter, search, and pinpoint state.
     - Line 46-52 & 77-83: Guards modals with authentication checks (`if (!user) navigate('/login');`).
   - `frontend/src/components/layout/Sidebar.jsx`:
     - Line 76-102: KUET branding header with "CampusShare KUET" and live `📍 700m Campus Perimeter` radar badge.
     - Line 110-143: Navigation tabs for `/` Map View ("God's Eye"), `/items` All Items ("Browse"), `/requests` Borrow Requests, and `/profile` My Profile ("Karma").
     - Line 147-205: Student card displaying student initials, name, roll, dept, `⚡ {user.karma ?? 100} Karma` badge, and logout action; prompts Log In / Register when unauthenticated.
   - `frontend/src/components/layout/TopActionBar.jsx`:
     - Line 62-82: Real-time search input with clear button.
     - Line 85-118: Segmented filter buttons for `All Items`, `🟢 Lending`, and `🚨 Beacons`.
     - Line 121-133: Category dropdown (`Calculators`, `Electronics & Power`, `Lab Equipment`, etc.).
     - Line 137-145: `+ Add Item` CTA button (`#btn-add-item-top`) invoking `onOpenAddModal`.

2. **Authentication & Roll Decoder**:
   - `frontend/src/App.jsx` (`Register` component):
     - Line 208-294: Form strictly contains **only 3 input fields**:
       1. Field 1 (Full Name): `<input type="text" ... value={name} onChange={...} required />`
       2. Field 2 (Email): `<input type="email" ... value={email} onChange={...} required />`
       3. Field 3 (Password): `<input type="password" ... value={password} onChange={...} required />`
     - Line 179-184: Submits strictly `{ name: name.trim(), email: email.trim().toLowerCase(), password }` to `api.post('/auth/register')`.
     - Line 39-79: `decodeKuetEmail` function parses prefix via regex `(\d{2})(\d{2})(\d{3})$`, maps department codes to names across 14 KUET departments, and returns decoded object.
     - Line 236-262: Live roll decoder badge dynamically displays `Batch: 20{batch}`, `Dept: {deptCode}`, `Roll: {roll}`, and `⚡ 100 Base Karma` as user types.

3. **KUET Karma Protocol UI Integration**:
   - `frontend/src/pages/Profile.jsx`:
     - Line 8-37: Renders Hero Karma Card: `⚡ {karma}` Protocol Score, net difference from Base (`{netKarmaChange >= 0 ? +... : ...} from Base`), total exchanges count.
     - Line 70-93: Displays KUET Karma Rules breakdown: `🟢 Lending an item: +10 Karma`, `⏱️ Returning on-time: +5 Karma`, `⚠️ Late return penalty: -30 Karma`, `🛡️ Initial registration base: 100 Karma`.
   - `frontend/src/pages/Transaction.jsx`:
     - Line 46-64: Processes return response payload `res.data?.karma_updated` and triggers notification toasts celebrating Karma updates.
     - Line 97-120: Renders celebration feedback card displaying Lender Award (`+{karmaResult.owner_gain} Karma ⚡`) and Borrower Change (`{karmaResult.borrower_change} Karma ⚡`).
     - Line 187: Action button: `Confirm Return & Update Karma ⚡`.
   - `frontend/src/pages/Requests.jsx`:
     - Line 57-69: Displays `⚡ {karmaScore} Karma` badge for requesting students and owners.
   - `frontend/src/pages/AllItems.jsx` & `frontend/src/components/items/ItemHoverCard.jsx`:
     - Line 31 & 153-157: `ItemHoverCard` renders `⚡ {ownerKarma} Karma` pill alongside student credentials.
   - `frontend/src/components/items/ItemCard.jsx`:
     - Line 20: Renders `⚡ {item.owner?.karma ?? item.karma ?? 100} Karma`.
   - `frontend/src/components/map/GodsEyeMap.jsx`:
     - Line 290 & 325: Renders MapLibre popup displaying `⚡ ${karmaScore} Karma`.
   - No legacy `trust_score` (4.5 / 5.0 scale) remains in user-facing views.

4. **Import Resolution**:
   - Checked all 24 source files (`.jsx` and `.js`) in `frontend/src/`.
   - All 101 static imports resolve without error:
     - 0 unresolved relative imports.
     - All external package imports (`@tanstack/react-query`, `axios`, `qrcode.react`, `react`, `react-dom`, `react-hot-toast`, `react-router-dom`) verified present in `frontend/node_modules`.

5. **Automated Suite Execution**:
   - `python3 Tanvir/verify_campus_map.py`:
     - Output: `TOTAL TESTS RUN: 95, PASSED: 95, FAILED: 0, ESTIMATED RUBRIC SCORE: 10.0 / 10.0`.
   - `python3 backend/test_m1.py`:
     - Output: `ALL MILESTONE 1 VERIFICATION TESTS PASSED SUCCESSFULLY!`.

---

## 2. Logic Chain

1. **R1 & R2 Layout & Navigation Conformance**:
   - *Observation*: `DashboardLayout.jsx` embeds `Sidebar` and `TopActionBar`, coordinates active view filters through `useDashboard()`, and manages modals (`AddItemModal`, `RequestModal`) locally.
   - *Inference*: The architecture fulfills R2 by replacing full-page redirects with modal popovers and providing a responsive, modern enterprise UI with clear KUET branding, search, and filtering.
2. **R3 Authentication & Roll Decoder Conformance**:
   - *Observation*: `App.jsx` `Register` component contains exactly 3 inputs (`name`, `email`, `password`) and excludes manual batch/dept/roll inputs. `decodeKuetEmail` validates `@stud.kuet.ac.bd` and extracts 7-digit IDs via regex `(\d{2})(\d{2})(\d{3})$`.
   - *Inference*: Students are not burdened with manual entry, and student credentials and starting 100 Karma are confirmed visually before submission.
3. **R4 KUET Karma Protocol Conformance**:
   - *Observation*: `Profile.jsx`, `Transaction.jsx`, `Requests.jsx`, `ItemHoverCard.jsx`, `ItemCard.jsx`, and `GodsEyeMap.jsx` display `⚡ {karma} Karma` and enforce the (+10 lend, +5 on-time, -30 late, 100 base) protocol rules.
   - *Inference*: The legacy 5-point trust rating has been cleanly replaced across the entire frontend application.
4. **Integrity & Quality Assessment**:
   - *Observation*: Code inspection reveals real React components, real state management, parameterized API calls, and zero hardcoded test pass bypasses.
   - *Inference*: The deliverable is authentic, robust, and free of integrity violations.

---

## 3. Caveats

1. **Host Environment**:
   - Node.js runtime is not available in the host terminal environment (`zsh: command not found: node`). Verification of JSX syntax, import resolution, and business logic was performed via static AST analysis, regex pattern matching, Python test drivers, and verified packages in `node_modules`.
2. **CDN Dependency for MapLibre**:
   - MapLibre GL JS and Turf.js are loaded via CDN scripts in `frontend/index.html`. `GodsEyeMap.jsx` includes retry timers and a spherical trigonometry fallback to maintain stability even if CDN loading experiences network latency.

---

## 4. Conclusion

**Verdict: APPROVE**

Milestone 2 (Frontend Dashboard layout, Authentication with KUET Roll Decoder, and KUET Karma UI) meets all specified requirements:
1. `DashboardLayout.jsx`, `Sidebar.jsx`, and `TopActionBar.jsx` provide a complete enterprise dashboard layout with KUET branding, navigation tabs, student Karma card, search/filter controls, and modal coordination without full-page navigation.
2. `Register` in `App.jsx` strictly has 3 input fields and features an active live roll decoder badge displaying Batch, Dept, Roll, and 100 Base Karma.
3. KUET Karma UI is cleanly integrated across `Profile.jsx`, `Transaction.jsx`, `Requests.jsx`, `AllItems.jsx`, `ItemHoverCard.jsx`, `ItemCard.jsx`, and `GodsEyeMap.jsx`.
4. All relative imports and package dependencies in `frontend/src/` resolve with 0 errors.
5. No integrity violations or hardcoded test bypasses were detected.

---

## 5. Verification Method

To independently reproduce the verification:

1. **Verify Register 3-Field Requirement & Decoder**:
   ```bash
   python3 -c "
   import re
   content = open('frontend/src/App.jsx').read()
   reg = re.search(r'function Register\(\) \{(.*?)\n\}', content, re.DOTALL).group(1)
   inputs = re.findall(r'<input\b[^>]*>', reg)
   assert len(inputs) == 3, f'Expected 3 inputs, found {len(inputs)}'
   assert 'api.post(\'/auth/register\'' in reg
   print('Register 3-field requirement PASSED!')
   "
   ```

2. **Verify Frontend Import Resolution**:
   ```bash
   python3 -c "
   import glob, os, re
   files = sorted(glob.glob('frontend/src/**/*.jsx', recursive=True) + glob.glob('frontend/src/**/*.js', recursive=True))
   unresolved = []
   for f in files:
       content = open(f).read()
       for imp in re.findall(r'(?:from|import)\s+[\'\"]([^\'\"]+)[\'\"]', content):
           if imp.startswith('.'):
               d = os.path.dirname(f)
               cands = [os.path.normpath(os.path.join(d, imp + ext)) for ext in ['', '.jsx', '.js', '.css', '/index.jsx', '/index.js']]
               if not any(os.path.isfile(c) for c in cands): unresolved.append((f, imp))
   assert len(unresolved) == 0, f'Unresolved: {unresolved}'
   print(f'Checked {len(files)} files: 0 unresolved imports!')
   "
   ```

3. **Verify Campus Map Test Suite**:
   ```bash
   python3 Tanvir/verify_campus_map.py
   ```
   *Expected Output*: `95 passed, 0 failed, ESTIMATED RUBRIC SCORE: 10.0 / 10.0`.

4. **Invalidation Conditions**:
   - Any added form field to `Register` beyond Name, Email, Password.
   - Any unresolved relative import or missing package in `frontend/src/`.
   - Any reintroduction of legacy 5.0 `trust_score` in place of `karma`.
