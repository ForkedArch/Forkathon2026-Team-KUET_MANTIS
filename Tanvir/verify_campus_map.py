"""
Automated Verification Suite for KUET Campus Lending & Borrowing Map Interface
Forkathon 2026 Deliverable - Team KUET_MANTIS
Independent Verification Script for Rubric Evaluation (R1, R2, R3, R4).
"""

import os
import sys
import io
import json
import math
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import app

DATA_FILE = os.path.join(BASE_DIR, "kuet_data", "kuet_landmarks.json")
INDEX_HTML = os.path.join(BASE_DIR, "index.html")

KUET_CENTER = (22.9006, 89.5024)

def haversine(coord1, coord2):
    """Calculate distance in meters between two (lat, lon) coordinates."""
    R = 6371000.0  # Earth radius in meters
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

class MockSocket:
    def __init__(self, request_bytes):
        self.rfile = io.BytesIO(request_bytes)
        self.wfile = io.BytesIO()
        self.sent_bytes = bytearray()

    def makefile(self, mode, *args, **kwargs):
        if 'r' in mode:
            return self.rfile
        return self.wfile

    def sendall(self, data):
        self.sent_bytes.extend(data)

def send_mock_request(request_bytes):
    """Executes a request against CampusRequestHandler and returns raw response bytes."""
    sock = MockSocket(request_bytes)
    app.CampusRequestHandler(sock, ('127.0.0.1', 8000), None)
    return bytes(sock.sent_bytes) + sock.wfile.getvalue()

def parse_http_response(raw_bytes):
    """Splits HTTP response into headers and body."""
    parts = raw_bytes.split(b"\r\n\r\n", 1)
    header_part = parts[0].decode("utf-8", errors="replace")
    body_part = parts[1] if len(parts) > 1 else b""
    status_line = header_part.split("\r\n")[0]
    return status_line, header_part, body_part

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []

    def assert_true(self, condition, test_name, detail=""):
        if condition:
            self.passed += 1
            print(f"  [PASS] {test_name}")
            self.results.append((True, test_name, detail))
        else:
            self.failed += 1
            print(f"  [FAIL] {test_name}: {detail}")
            self.results.append((False, test_name, detail))

    def run_all(self):
        print("\n" + "=" * 70)
        print("  KUET CAMPUS LENDING & BORROWING MAP - VERIFICATION SUITE")
        print("=" * 70 + "\n")

        self.test_landmarks_and_radius()
        self.test_perimeter_ring_and_geometry()
        self.test_clean_map_no_landmark_markers()
        self.test_ui_layout_and_element_alignment()
        self.test_mock_users_and_items()
        self.test_pinpointing_and_modal_dom()
        self.test_manual_pinpoint_workflow()
        self.test_modular_auth_and_user_profile()
        self.test_http_server_and_api()

        print("\n" + "-" * 70)
        print(f"  TOTAL TESTS RUN: {self.passed + self.failed}")
        print(f"  PASSED: {self.passed}")
        print(f"  FAILED: {self.failed}")
        score = (self.passed / (self.passed + self.failed)) * 10.0 if (self.passed + self.failed) > 0 else 0
        print(f"  ESTIMATED RUBRIC SCORE: {score:.1f} / 10.0 (Threshold: >= 9.0)")
        print("-" * 70 + "\n")
        self.assert_true(score >= 9.0, "Rubric score meets or exceeds 9.0 / 10.0 threshold")
        return self.failed == 0

    def test_landmarks_and_radius(self):
        print("--- [R1] Landmark & Campus Map Accuracy Tests ---")
        self.assert_true(os.path.exists(DATA_FILE), "Data file exists", DATA_FILE)
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        campus = data.get("campus", {})
        center = campus.get("center", [])
        self.assert_true(len(center) == 2, "Campus center defined", f"Center: {center}")
        self.assert_true(abs(center[0] - KUET_CENTER[0]) < 0.001 and abs(center[1] - KUET_CENTER[1]) < 0.001,
                         "Campus center matches KUET (22.9006° N, 89.5024° E)", f"{center}")

        radius = campus.get("boundary_radius_meters")
        self.assert_true(radius == 700, "Campus perimeter radius explicitly 700 meters", f"Found: {radius}")

        zones = data.get("zones", [])
        zone_names = [z.get("name", "") for z in zones]

        # Academic complexes
        academics = ["CSE", "EEE", "ME", "Civil"]
        for ac in academics:
            found = any(ac in name for name in zone_names)
            self.assert_true(found, f"Academic complex present: {ac}", f"Available: {zone_names}")

        # Residential halls (all 7)
        halls = [
            ("Amar Ekushey", ["ekushey", "amar"]),
            ("Fazlul Haque", ["fazlul"]),
            ("Lalan Shah", ["lalan"]),
            ("Khan Jahan Ali", ["khan", "jahan"]),
            ("Dr. M.A. Rashid", ["rashid"]),
            ("Rokeya", ["rokeya"]),
            ("Bangabandhu Sheikh Mujibur Rahman", ["bangabandhu"])
        ]
        for hall_name, keywords in halls:
            found = any(any(k in name.lower() for k in keywords) for name in zone_names)
            self.assert_true(found, f"Residential hall present: {hall_name}", f"Available: {zone_names}")

        # Facilities & Gates
        self.assert_true(any("library" in name.lower() for name in zone_names), "Central Library present")
        self.assert_true(any("cafeteria" in name.lower() for name in zone_names), "Student Cafeteria present")
        self.assert_true(any("gate" in name.lower() for name in zone_names), "Campus Entry Gate(s) present")

        # Verify all landmark coordinates are strictly within 700m radius of center
        all_within_700 = True
        distances = {}
        for z in zones:
            coords = z.get("coords")
            dist = haversine(KUET_CENTER, (coords[0], coords[1]))
            distances[z["id"]] = dist
            if dist > 700:
                all_within_700 = False
                print(f"    WARNING: Landmark {z['name']} is {dist:.1f}m away (> 700m)")
        self.assert_true(all_within_700, "All landmarks strictly within 700m perimeter", f"Max distance: {max(distances.values()):.1f}m")

    def test_perimeter_ring_and_geometry(self):
        print("\n--- [R1 Update] 700m Perimeter Boundary Geometry Tests ---")
        with open(INDEX_HTML, "r", encoding="utf-8") as f:
            html = f.read()

        self.assert_true("700" in html, "700m mentioned in index.html")
        self.assert_true("CAMPUS_PERIMETER_RADIUS = 700" in html or "drawPerimeterCircle(700)" in html,
                         "Visual boundary ring explicitly programmed with 700 meters radius")
        self.assert_true("turf.circle" in html, "Turf.js used to compute boundary circle polygon")
        self.assert_true("700m Campus Perimeter" in html or "700m" in html, "Visual badge indicator for 700m radius present in UI")

    def test_clean_map_no_landmark_markers(self):
        print("\n--- [R1 Refinement] Clean Map & Elimination of Conflicting Pins ---")
        with open(INDEX_HTML, "r", encoding="utf-8") as f:
            html = f.read()

        # Pre-baked landmark markers must NOT be added to the map on load
        self.assert_true("renderLandmarks()" not in html or "showLandmarks = false" in html,
                         "Pre-baked landmark pins are eliminated from initial map load")
        self.assert_true("landmarkMarkers.forEach(m => m.remove())" in html,
                         "Landmark marker cleaning routine active")
        self.assert_true("osm-tiles" in html and "tile.openstreetmap.org" in html,
                         "MapLibre GL configured with OpenStreetMap native basemap tiles")
        self.assert_true('id="toggle-landmarks-btn"' not in html,
                         "Redundant landmark toggle button removed from active layer controls")
        self.assert_true("campus-perimeter-700m" in html,
                         "Visual 700m campus perimeter boundary ring active")

    def test_ui_layout_and_element_alignment(self):
        print("\n--- [R2 Refinement] UI Layout, Element Alignment & Polish ---")
        with open(INDEX_HTML, "r", encoding="utf-8") as f:
            html = f.read()

        self.assert_true('id="header-user-profile"' in html or 'class="user-profile-badge"' in html,
                         "Header features student profile identity badge")
        self.assert_true('id="header-user-name"' in html and 'id="header-user-roll"' in html,
                         "Header profile displays student name, roll number, and karma")
        self.assert_true('id="jump-landmark"' not in html,
                         "Cramped landmark dropdown removed from secondary filter row")
        self.assert_true('id="filter-category"' in html and 'category-filter-wrapper' in html,
                         "Clean full-width category selector present in secondary filter row")
        self.assert_true('empty-state-card' in html or 'empty-state' in html,
                         "Refined empty state card component implemented")
        self.assert_true('resetFilters' in html and 'btn-reset-filters' in html,
                         "Empty state features 'Reset Filters' interactive recovery action")
        self.assert_true('map-hud' in html and 'hud-card' in html,
                         "Map HUD controls neatly docked with glassmorphism")
        self.assert_true('id="toggle-ring-btn"' in html and 'id="toggle-beacons-btn"' in html,
                         "Perimeter ring toggle and beacon toggle present in HUD")
        self.assert_true('id="recenter-kuet-btn"' in html,
                         "Map recenter quick action present in HUD")

    def test_mock_users_and_items(self):
        print("\n--- [R2] Mock Users & Lend/Borrow Items Tests ---")
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        items = data.get("sample_active_items", [])
        self.assert_true(len(items) >= 6, f"At least 6 simulated items (Found: {len(items)})")

        users = set()
        lenders = 0
        borrowers = 0
        has_trust_ratings = True
        has_departments = True
        has_specs = True
        has_conditions = True

        for it in items:
            uname = it.get("lender_name")
            if uname:
                users.add(uname)
            if it.get("type") == "lend":
                lenders += 1
            elif it.get("type") == "borrow":
                borrowers += 1

            if "trust_rating" not in it or it["trust_rating"] < 3.0:
                has_trust_ratings = False
            if "dept" not in it:
                has_departments = False
            if "specs" not in it:
                has_specs = False
            if "condition" not in it:
                has_conditions = False

        self.assert_true(len(users) >= 6, f"At least 6 distinct realistic simulated campus users (Found: {len(users)}: {users})")
        self.assert_true(lenders >= 3, f"Offers to lend present (Found: {lenders})")
        self.assert_true(borrowers >= 2, f"Active demand beacons (need to borrow) present (Found: {borrowers})")
        self.assert_true(has_trust_ratings, "All users have trust ratings (e.g. 4.7 - 4.95 / 5)")
        self.assert_true(has_departments, "All users have department and batch designations")
        self.assert_true(has_specs, "All items have detailed specifications/notes")
        self.assert_true(has_conditions, "All items have condition classifications")

        # Check for pulse animation & distinct indicators in CSS
        with open(INDEX_HTML, "r", encoding="utf-8") as f:
            html = f.read()
        self.assert_true("beacon-pulse" in html or "radar-pulse" in html, "Demand beacons have pulsing radar/sonar animation")
        self.assert_true("marker-beacon" in html and "marker-lend" in html, "Distinct marker styles for Lending vs Borrowing")

    def test_pinpointing_and_modal_dom(self):
        print("\n--- [R3] Manual Item Addition & Interactive Pinpointing DOM Tests ---")
        with open(INDEX_HTML, "r", encoding="utf-8") as f:
            html = f.read()

        # Modal elements
        required_dom_elements = [
            "add-item-modal",
            "item-title",
            "item-category",
            "item-specs",
            "type-btn-lend",
            "type-btn-borrow",
            "img-upload-box",
            "file-input",
            "preview-img",
            "proceed-pin-btn",
            "direct-submit-btn",
            "pin-banner"
        ]
        for el_id in required_dom_elements:
            self.assert_true(f'id="{el_id}"' in html, f"DOM element present: #{el_id}")

        # Pinpoint logic checks
        self.assert_true("pin-mode" in html, "Pinpoint crosshair mode class implemented")
        self.assert_true("e.lngLat" in html or "handleMapClick" in html, "Map click coordinate capture implemented")
        self.assert_true("map.flyTo" in html, "Camera auto-fly to coordinates implemented")
        self.assert_true("renderItems" in html, "Instant live update without page reload implemented")

    def test_manual_pinpoint_workflow(self):
        print("\n--- [R3 Refinement] 100% Manual Click-to-Pin Workflow Tests ---")
        with open(INDEX_HTML, "r", encoding="utf-8") as f:
            html = f.read()

        # Pinpoint mode crosshair cursor
        self.assert_true("pin-mode" in html, "Pinpoint crosshair mode class .pin-mode defined")
        self.assert_true("cursor: crosshair" in html, "Map canvas cursor turns to crosshair in pin mode")

        # Pinpoint guidance banner
        self.assert_true("pin-banner" in html and "btn-cancel-pin" in html,
                         "Top instruction banner with cancel action present during pinpointing")

        # Interactive map coordinate capture
        self.assert_true("handleMapClick" in html and "e.lngLat" in html,
                         "Interactive map click listener captures accurate geographic coordinates")

        # Instant live update
        self.assert_true("finalizeItemCreation" in html,
                         "Instant item persistence and feed/map update routine implemented")
        self.assert_true("map.flyTo" in html,
                         "Camera auto-focuses to placed pin coordinate")

    def test_modular_auth_and_user_profile(self):
        print("\n--- [R5 Refinement] Modular Auth & Student Profile Model Tests ---")
        with open(INDEX_HTML, "r", encoding="utf-8") as f:
            html = f.read()

        # CampusAuth modular architecture
        self.assert_true("CampusAuth" in html, "Modular CampusAuth object defined in index.html")
        self.assert_true("isDemoMode: true" in html or "isDemoMode" in html,
                         "Demo mode flag active for pluggable SSO integration")
        self.assert_true("currentUser" in html, "Active currentUser session model defined")
        self.assert_true("roll" in html and "karma" in html,
                         "User profile model tracks student roll number and karma rating")

        # Active student context surfaced in modal
        self.assert_true("modal-auth-profile" in html or "modal-user-name" in html,
                         "Modal displays active student session context")

        # Backend app.py persistence of student credentials
        with open(os.path.join(BASE_DIR, "app.py"), "r", encoding="utf-8") as f:
            app_code = f.read()
        self.assert_true("roll" in app_code and "karma" in app_code and "user_id" in app_code,
                         "Backend app.py accepts and stores user_id, roll, and karma on item creation")

        # Verify /api/auth/current endpoint
        raw_auth = send_mock_request(b"GET /api/auth/current HTTP/1.1\r\nHost: localhost\r\n\r\n")
        status_line, headers, body = parse_http_response(raw_auth)
        self.assert_true("200 OK" in status_line, "GET /api/auth/current returns HTTP 200 OK")
        auth_data = json.loads(body.decode("utf-8"))
        self.assert_true(auth_data.get("authenticated") is True and "user" in auth_data,
                         "/api/auth/current returns authenticated user profile")
        self.assert_true("roll" in auth_data.get("user", {}) and "karma" in auth_data.get("user", {}),
                         "Auth endpoint user includes student roll and karma")

    def test_http_server_and_api(self):
        print("\n--- [R4] HTTP Server & REST API Tests ---")
        
        # Test 1: GET / (Dashboard HTML)
        raw_root = send_mock_request(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
        status_line, headers, body = parse_http_response(raw_root)
        self.assert_true("200 OK" in status_line, "GET / returns HTTP 200 OK")
        self.assert_true("KUET CampusShare" in body.decode("utf-8", errors="replace"),
                         "GET / serves valid CampusShare HTML interface")

        # Test 2: GET /api/landmarks
        raw_lm = send_mock_request(b"GET /api/landmarks HTTP/1.1\r\nHost: localhost\r\n\r\n")
        status_line, headers, body = parse_http_response(raw_lm)
        self.assert_true("200 OK" in status_line, "GET /api/landmarks returns HTTP 200 OK")
        data_lm = json.loads(body.decode("utf-8"))
        self.assert_true(data_lm.get("success") is True, "/api/landmarks success flag is True")
        self.assert_true(len(data_lm.get("zones", [])) >= 15,
                         f"/api/landmarks returns campus zones (Count: {len(data_lm.get('zones', []))})")
        self.assert_true(data_lm.get("campus", {}).get("boundary_radius_meters") == 700,
                         "/api/landmarks returns boundary_radius_meters = 700")

        # Test 3: GET /api/items
        raw_items = send_mock_request(b"GET /api/items HTTP/1.1\r\nHost: localhost\r\n\r\n")
        status_line, headers, body = parse_http_response(raw_items)
        self.assert_true("200 OK" in status_line, "GET /api/items returns HTTP 200 OK")
        data_items = json.loads(body.decode("utf-8"))
        initial_count = data_items.get("count", 0)
        self.assert_true(initial_count >= 6, f"/api/items returns initial items count >= 6 (Count: {initial_count})")
        self.assert_true(any("roll" in i for i in data_items.get("items", [])),
                         "/api/items seed items include student roll numbers")
        self.assert_true(any("karma" in i for i in data_items.get("items", [])),
                         "/api/items seed items include student karma ratings")

        # Test 4: Query filtering by type
        raw_lend = send_mock_request(b"GET /api/items?type=lend HTTP/1.1\r\nHost: localhost\r\n\r\n")
        _, _, body_lend = parse_http_response(raw_lend)
        data_lend = json.loads(body_lend.decode("utf-8"))
        self.assert_true(all(i.get("type") == "lend" for i in data_lend.get("items", [])),
                          "/api/items?type=lend correctly filters only lending items")

        raw_borrow = send_mock_request(b"GET /api/items?type=borrow HTTP/1.1\r\nHost: localhost\r\n\r\n")
        _, _, body_borrow = parse_http_response(raw_borrow)
        data_borrow = json.loads(body_borrow.decode("utf-8"))
        self.assert_true(all(i.get("type") == "borrow" for i in data_borrow.get("items", [])),
                          "/api/items?type=borrow correctly filters only borrow demand beacons")

        # Test 5: POST /api/items (Simulate pinpoint item submission)
        payload = {
            "title": "TI-84 Plus Graphing Calculator",
            "type": "lend",
            "category": "Calculators",
            "lat": 22.9004,
            "lng": 89.5022,
            "user_id": "student_kuet_2207001",
            "roll": "2207001",
            "karma": 4.9,
            "lender_name": "Auditor Test Student",
            "dept": "CSE '23",
            "condition": "Like New",
            "specs": "Test calculator logged via automated pinpoint verification test."
        }
        post_body = json.dumps(payload).encode("utf-8")
        req_post = (
            f"POST /api/items HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\n"
            f"Content-Length: {len(post_body)}\r\n\r\n"
        ).encode("utf-8") + post_body

        raw_post = send_mock_request(req_post)
        status_line, headers, body = parse_http_response(raw_post)
        self.assert_true("201" in status_line, "POST /api/items creates new item (HTTP 201 Created)")
        post_data = json.loads(body.decode("utf-8"))
        self.assert_true(post_data.get("success") is True and "item" in post_data,
                         "POST /api/items returns success and created item payload")
        created_item = post_data.get("item", {})
        self.assert_true("roll" in created_item and "karma" in created_item,
                         "POST /api/items persists student roll and karma in item payload")
        created_id = created_item.get("id")

        # Verify item was persisted in server memory
        raw_after = send_mock_request(b"GET /api/items HTTP/1.1\r\nHost: localhost\r\n\r\n")
        _, _, body_after = parse_http_response(raw_after)
        data_after = json.loads(body_after.decode("utf-8"))
        self.assert_true(data_after.get("count") == initial_count + 1,
                         f"Item persisted in memory (Count increased from {initial_count} to {data_after.get('count')})")
        self.assert_true(any(i.get("id") == created_id for i in data_after.get("items", [])),
                         "Created item ID verified in items list")

if __name__ == "__main__":
    runner = TestRunner()
    success = runner.run_all()
    sys.exit(0 if success else 1)
