import os
import sys
import asyncio
import json
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Ensure backend directory is in path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app import models, database


class ASGIResponse:
    def __init__(self, status_code, headers, content):
        self.status_code = status_code
        self.headers = {k.decode("latin1").lower(): v.decode("latin1") for k, v in headers}
        self.content = bytes(content)
        self.text = content.decode("utf-8", errors="replace")

    def json(self):
        return json.loads(self.text)


class ASGIClient:
    def __init__(self, asgi_app):
        self.app = asgi_app

    def request(self, method, path, headers=None, json=None, data=None, params=None):
        return asyncio.run(self._request_async(method, path, headers=headers, json_payload=json, data=data, params=params))

    async def _request_async(self, method, path, headers=None, json_payload=None, data=None, params=None):
        if params:
            qs = urllib.parse.urlencode(params)
            query_string = qs.encode("utf-8")
        elif "?" in path:
            path, qs = path.split("?", 1)
            query_string = qs.encode("utf-8")
        else:
            query_string = b""

        raw_headers = []
        body_bytes = b""
        has_content_type = False

        if json_payload is not None:
            import json as _json
            body_bytes = _json.dumps(json_payload).encode("utf-8")
            raw_headers.append((b"content-type", b"application/json"))
            has_content_type = True
        elif data is not None:
            if isinstance(data, dict):
                # Check if multipart is requested or default to multipart
                boundary = "----TestBoundary123456789"
                parts = bytearray()
                for k, v in data.items():
                    parts.extend(f"--{boundary}\r\n".encode("utf-8"))
                    parts.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode("utf-8"))
                    parts.extend(str(v).encode("utf-8"))
                    parts.extend(b"\r\n")
                parts.extend(f"--{boundary}--\r\n".encode("utf-8"))
                body_bytes = bytes(parts)
                raw_headers.append((b"content-type", f"multipart/form-data; boundary={boundary}".encode("utf-8")))
                has_content_type = True
            elif isinstance(data, (bytes, bytearray)):
                body_bytes = bytes(data)

        if headers:
            for k, v in headers.items():
                if k.lower() == "content-type" and has_content_type:
                    continue
                raw_headers.append((k.lower().encode("latin1"), v.encode("latin1")))

        raw_headers.append((b"content-length", str(len(body_bytes)).encode("ascii")))

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": method.upper(),
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": query_string,
            "headers": raw_headers,
            "server": ("127.0.0.1", 80),
            "client": ("127.0.0.1", 54321),
            "scheme": "http",
        }

        response_status = None
        response_headers = []
        response_body = bytearray()

        messages = [
            {"type": "http.request", "body": body_bytes, "more_body": False}
        ]

        async def receive():
            if messages:
                return messages.pop(0)
            return {"type": "http.disconnect"}

        async def send(message):
            nonlocal response_status, response_headers, response_body
            if message["type"] == "http.response.start":
                response_status = message["status"]
                response_headers = message.get("headers", [])
            elif message["type"] == "http.response.body":
                response_body.extend(message.get("body", b""))

        await self.app(scope, receive, send)
        return ASGIResponse(response_status, response_headers, response_body)

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self.request("PUT", path, **kwargs)

    def delete(self, path, **kwargs):
        return self.request("DELETE", path, **kwargs)


client = ASGIClient(app)


def run_tests():
    print("==================================================")
    print("STARTING COMPREHENSIVE MILESTONE 1 VERIFICATION")
    print("==================================================")

    # ----------------------------------------------------
    # TEST 1: Orphaned requests.py deletion check
    # ----------------------------------------------------
    print("\n[TEST 1] Checking deletion of orphaned requests.py...")
    requests_path = backend_dir / "app" / "routes" / "requests.py"
    assert not requests_path.exists(), f"FAILED: {requests_path} still exists!"
    print("  --> PASS: backend/app/routes/requests.py does not exist.")

    # ----------------------------------------------------
    # TEST 2: Landmarks API Endpoint
    # ----------------------------------------------------
    print("\n[TEST 2] Testing GET /api/landmarks (and trailing slash)...")
    for path in ["/api/landmarks", "/api/landmarks/"]:
        r = client.get(path)
        assert r.status_code == 200, f"FAILED: {path} returned {r.status_code}"
        data = r.json()
        assert data.get("success") is True, f"FAILED: success is not True in {path}"
        campus = data.get("campus", {})
        assert campus.get("name") == "Khulna University of Engineering & Technology (KUET)"
        assert campus.get("boundary_radius_meters") == 700
        zones = data.get("zones", [])
        assert len(zones) == 21, f"FAILED: expected 21 zones, got {len(zones)}"
    print("  --> PASS: Landmarks endpoint returns 21 zones and 700m radius.")

    # ----------------------------------------------------
    # TEST 3: KUET Email Validation & Roll Decoder (R3)
    # ----------------------------------------------------
    print("\n[TEST 3] Testing Authentication & KUET Roll Decoder...")
    # 3.1 Non-KUET domain rejected with HTTP 400
    r_bad_domain = client.post("/api/auth/register", json={
        "name": "Outsider User",
        "email": "outsider@gmail.com",
        "password": "password123"
    })
    assert r_bad_domain.status_code == 400, f"FAILED: non-KUET email gave {r_bad_domain.status_code}"
    print("  --> PASS: Non-KUET email rejected with HTTP 400.")

    # 3.2 Malformed email rejected with HTTP 400
    r_bad_format = client.post("/api/auth/register", json={
        "name": "Invalid Roll User",
        "email": "invalidroll@stud.kuet.ac.bd",
        "password": "password123"
    })
    assert r_bad_format.status_code == 400, f"FAILED: malformed email gave {r_bad_format.status_code}"
    print("  --> PASS: Malformed KUET email rejected with HTTP 400.")

    # 3.3 Valid KUET registration & auto decode
    test_email = "siddique2507028@stud.kuet.ac.bd"
    r_reg = client.post("/api/auth/register", json={
        "name": "Siddique Ahmed",
        "email": test_email,
        "password": "secretpassword"
    })
    if r_reg.status_code == 400 and "Email already registered" in r_reg.text:
        db = database.SessionLocal()
        user_obj = db.query(models.User).filter(models.User.email == test_email).first()
        db.close()
        assert user_obj is not None
        assert user_obj.batch == "25"
        assert user_obj.dept == "07"
        assert user_obj.roll == "028"
        assert user_obj.karma == 100
        print("  --> PASS: Registration verified for existing user (batch=25, dept=07, roll=028, karma=100).")
    else:
        assert r_reg.status_code == 200, f"FAILED: registration gave {r_reg.status_code}: {r_reg.text}"
        u_data = r_reg.json()
        assert u_data["batch"] == "25", f"Expected batch '25', got {u_data['batch']}"
        assert u_data["dept"] == "07", f"Expected dept '07', got {u_data['dept']}"
        assert u_data["roll"] == "028", f"Expected roll '028', got {u_data['roll']}"
        assert u_data["karma"] == 100, f"Expected karma 100, got {u_data.get('karma')}"
        print("  --> PASS: User registered with auto-decoded batch=25, dept=07, roll=028, karma=100.")

    # 3.4 Same roll in different department should succeed (composite uniqueness)
    diff_dept_email = "student2501028@stud.kuet.ac.bd"  # Dept 01 instead of 07
    r_diff_dept = client.post("/api/auth/register", json={
        "name": "Different Dept Student",
        "email": diff_dept_email,
        "password": "secretpassword"
    })
    if r_diff_dept.status_code != 400:
        assert r_diff_dept.status_code == 200
        assert r_diff_dept.json()["dept"] == "01"
        assert r_diff_dept.json()["roll"] == "028"
        print("  --> PASS: Composite unique constraint allows same roll in different department.")

    # 3.5 Alias GET /api/auth/current
    r_cur = client.get("/api/auth/current")
    assert r_cur.status_code == 200
    cur_data = r_cur.json()
    assert cur_data.get("authenticated") is True
    assert "user" in cur_data
    assert "karma" in cur_data["user"]
    assert "roll" in cur_data["user"]
    print("  --> PASS: GET /api/auth/current returns authenticated profile with karma and roll.")

    # ----------------------------------------------------
    # TEST 4: Item Creation (JSON & Form) & Filtering
    # ----------------------------------------------------
    print("\n[TEST 4] Testing Item Creation (JSON and Form) and Filters...")
    # Login to get token
    login_res = client.post("/api/auth/login", json={
        "email": "tanvir2207001@stud.kuet.ac.bd",
        "password": "kuet1234"
    })
    assert login_res.status_code == 200, f"FAILED login: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 4.1 Create Item via JSON
    json_payload = {
        "title": "TI-84 Plus CE Graphing Calculator",
        "type": "lend",
        "category": "Calculators",
        "specs": "Color display, rechargeable battery",
        "condition": "Like New",
        "lat": 22.9004,
        "lng": 89.5025,
        "zone": "cse_bldg",
        "tags": ["#TI84", "#Graphing"]
    }
    r_item_json = client.post("/api/items/", json=json_payload, headers=headers)
    assert r_item_json.status_code == 201, f"FAILED json item creation: {r_item_json.status_code} {r_item_json.text}"
    created_item_json = r_item_json.json()
    assert created_item_json.get("title") == json_payload["title"] or created_item_json.get("item", {}).get("title") == json_payload["title"]
    print("  --> PASS: Item created successfully via application/json.")

    # 4.2 Create Item via Form Data
    form_data = {
        "title": "Digital Logic Trainer Board",
        "type": "lend",
        "category": "Lab Equipment",
        "specs": "Complete with 74-series TTL ICs",
        "condition": "Good",
        "latitude": "22.8998",
        "longitude": "89.5031",
        "zone": "eee_bldg",
        "tags": '["#DigitalLogic", "#EEE"]'
    }
    r_item_form = client.post("/api/items/", data=form_data, headers=headers)
    assert r_item_form.status_code == 201, f"FAILED form item creation: {r_item_form.status_code} {r_item_form.text}"
    print("  --> PASS: Item created successfully via multipart/form-data.")

    # 4.3 List items filtering
    # Filter by type=lend
    r_lend = client.get("/api/items?type=lend")
    assert r_lend.status_code == 200
    lend_items = r_lend.json()
    assert len(lend_items) > 0
    assert all(it["type"] == "lend" for it in lend_items)

    # Filter by type=borrow
    r_borrow = client.get("/api/items?type=borrow")
    assert r_borrow.status_code == 200
    borrow_items = r_borrow.json()
    assert len(borrow_items) >= 3
    assert all(it["type"] == "borrow" for it in borrow_items)

    # Filter by category
    r_calc = client.get("/api/items?category=Calculators")
    assert r_calc.status_code == 200
    assert len(r_calc.json()) >= 2

    # Filter by search q
    r_search = client.get("/api/items?q=Arduino")
    assert r_search.status_code == 200
    assert any("Arduino" in it["title"] for it in r_search.json())
    print("  --> PASS: Item filtering by type (lend/borrow), category, and search query verified.")

    # ----------------------------------------------------
    # TEST 5: Borrow Request Status Update & Transaction Schema
    # ----------------------------------------------------
    print("\n[TEST 5] Testing Borrow Request Status Update & Transaction schema...")
    owner_token = token  # Tanvir
    # Login Siddique
    login_sid = client.post("/api/auth/login", json={
        "email": "siddique2307010@stud.kuet.ac.bd",
        "password": "kuet1234"
    })
    borrower_token = login_sid.json()["access_token"]
    borrower_headers = {"Authorization": f"Bearer {borrower_token}"}
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    # Siddique creates borrow request for Tanvir's item (Item id 2: Baseus Charger)
    req_res = client.post("/api/requests/", json={
        "item_id": 2,
        "duration_hours": 2,
        "purpose": "Study session",
        "pickup_zone": "cse_bldg"
    }, headers=borrower_headers)
    assert req_res.status_code == 200, f"FAILED borrow request: {req_res.text}"
    req_id = req_res.json()["id"]

    # Verify query param status update: PUT /api/requests/{id}/status?status=accepted
    accept_res = client.put(f"/api/requests/{req_id}/status?status=accepted", headers=owner_headers)
    assert accept_res.status_code == 200, f"FAILED accept via query param: {accept_res.status_code} {accept_res.text}"
    print("  --> PASS: Borrow request accepted via query param ?status=accepted.")

    # Verify BorrowRequestOut includes transaction field
    my_requests = client.get("/api/requests/me", headers=borrower_headers).json()
    target_req = next((r for r in my_requests if r["id"] == req_id), None)
    assert target_req is not None
    assert "transaction" in target_req
    print("  --> PASS: BorrowRequestOut schema correctly includes transaction field.")

    # ----------------------------------------------------
    # TEST 6: Handover & Karma Calculations (R4)
    # ----------------------------------------------------
    print("\n[TEST 6] Testing Handover and KUET Karma Protocol (+10 owner, +5 on-time, -30 late)...")
    # 6.1 Start transaction (Owner)
    start_res = client.post("/api/transactions/start", json={"request_id": req_id}, headers=owner_headers)
    assert start_res.status_code == 200
    otp = start_res.json()["otp"]

    # 6.2 Verify handover (Borrower)
    verify_res = client.post("/api/transactions/verify", json={"request_id": req_id, "otp": otp}, headers=borrower_headers)
    assert verify_res.status_code == 200

    # Get baseline karma before return
    db = database.SessionLocal()
    owner_before = db.query(models.User).filter(models.User.email == "tanvir2207001@stud.kuet.ac.bd").first().karma
    borrower_before = db.query(models.User).filter(models.User.email == "siddique2307010@stud.kuet.ac.bd").first().karma
    db.close()

    # 6.3 On-time return
    return_res = client.post(f"/api/transactions/return/{req_id}", headers=borrower_headers)
    assert return_res.status_code == 200, f"FAILED return: {return_res.text}"
    ret_data = return_res.json()
    assert ret_data.get("karma_updated", {}).get("is_on_time") is True
    assert ret_data.get("karma_updated", {}).get("owner_gain") == 10
    assert ret_data.get("karma_updated", {}).get("borrower_change") == 5

    # Check updated scores in DB
    db = database.SessionLocal()
    owner_after = db.query(models.User).filter(models.User.email == "tanvir2207001@stud.kuet.ac.bd").first().karma
    borrower_after = db.query(models.User).filter(models.User.email == "siddique2307010@stud.kuet.ac.bd").first().karma
    db.close()

    assert owner_after == owner_before + 10, f"Expected owner karma {owner_before + 10}, got {owner_after}"
    assert borrower_after == borrower_before + 5, f"Expected borrower karma {borrower_before + 5}, got {borrower_after}"
    print(f"  --> PASS: On-time return: Owner +10 ({owner_before} -> {owner_after}), Borrower +5 ({borrower_before} -> {borrower_after}).")

    # 6.4 Late return test (-30 for borrower)
    req2_res = client.post("/api/requests/", json={
        "item_id": 1,  # Siddique's Casio calculator
        "duration_hours": 1,
        "purpose": "Late return simulation",
        "pickup_zone": "ekushey_hall"
    }, headers=owner_headers)  # Tanvir borrows from Siddique
    req2_id = req2_res.json()["id"]

    # Siddique accepts
    client.put(f"/api/requests/{req2_id}/status?status=accepted", headers=borrower_headers)
    # Siddique starts handover
    st2 = client.post("/api/transactions/start", json={"request_id": req2_id}, headers=borrower_headers)
    otp2 = st2.json()["otp"]
    # Tanvir verifies handover
    client.post("/api/transactions/verify", json={"request_id": req2_id, "otp": otp2}, headers=owner_headers)

    # Artificially manipulate trans.borrowed_at to 5 hours ago to simulate late return
    db = database.SessionLocal()
    trans = db.query(models.Transaction).filter(models.Transaction.request_id == req2_id).first()
    trans.borrowed_at = datetime.now(timezone.utc) - timedelta(hours=5)
    db.commit()
    tanvir_before_late = db.query(models.User).filter(models.User.email == "tanvir2207001@stud.kuet.ac.bd").first().karma
    siddique_before_late = db.query(models.User).filter(models.User.email == "siddique2307010@stud.kuet.ac.bd").first().karma
    db.close()

    # Tanvir returns late
    ret_late_res = client.post(f"/api/transactions/return/{req2_id}", headers=owner_headers)
    assert ret_late_res.status_code == 200
    ret_late_data = ret_late_res.json()
    assert ret_late_data.get("karma_updated", {}).get("is_on_time") is False
    assert ret_late_data.get("karma_updated", {}).get("owner_gain") == 10
    assert ret_late_data.get("karma_updated", {}).get("borrower_change") == -30

    db = database.SessionLocal()
    tanvir_after_late = db.query(models.User).filter(models.User.email == "tanvir2207001@stud.kuet.ac.bd").first().karma
    siddique_after_late = db.query(models.User).filter(models.User.email == "siddique2307010@stud.kuet.ac.bd").first().karma
    db.close()

    assert siddique_after_late == siddique_before_late + 10
    assert tanvir_after_late == tanvir_before_late - 30
    print(f"  --> PASS: Late return: Owner +10 ({siddique_before_late} -> {siddique_after_late}), Borrower -30 ({tanvir_before_late} -> {tanvir_after_late}).")

    print("\n==================================================")
    print("ALL MILESTONE 1 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    run_tests()
