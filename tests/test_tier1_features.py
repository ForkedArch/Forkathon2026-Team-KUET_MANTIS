"""
Tier 1: Feature Coverage (>=5 tests per core feature)
Happy-path isolation tests for all core KUET CampusShare features:
- Auth & Identity (5 tests)
- Roll Decoding & Department Mapping (5 tests)
- Item Listings & Demand Beacons (5 tests)
- Search & Filters (5 tests)
- Borrow Requests Lifecycle (5 tests)
- Handover OTP/QR Verification (5 tests)
- Return & Karma Calculations (5 tests)
- Messaging & Conversations (5 tests)
- In-App Notifications (5 tests)
- Peer Reviews & Ratings (5 tests)
- Campus Landmarks & Coordinates (5 tests)
Total: 55 tests
"""

import datetime
from tests.base import BaseE2ETestCase
from app import models


class TestTier1Features(BaseE2ETestCase):

    # =========================================================================
    # 1. Auth & Identity (Features 4, 5, 6)
    # =========================================================================

    def test_01_student_registration_success(self):
        """Student registration with valid @stud.kuet.ac.bd email returns 200, user id, and base karma."""
        resp = self.register_user(
            name="Tanvir Hossain",
            email="tanvir2107001@stud.kuet.ac.bd",
            password="SecurePassword123!",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("id", data)
        self.assertEqual(data["name"], "Tanvir Hossain")
        self.assertEqual(data["email"], "tanvir2107001@stud.kuet.ac.bd")
        self.assertEqual(data["karma"], 100)
        self.assertEqual(data["trust_score"], 100.0)
        self.assertEqual(data["total_lends"], 0)
        self.assertEqual(data["total_borrows"], 0)

    def test_02_student_login_success(self):
        """Valid credentials return JWT access token of bearer type and user payload."""
        self.register_user(
            name="Abdur Siddique",
            email="siddique2307010@stud.kuet.ac.bd",
            password="MySecretPassword1",
        )
        resp = self.login_user(
            email="siddique2307010@stud.kuet.ac.bd",
            password="MySecretPassword1",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["user"]["email"], "siddique2307010@stud.kuet.ac.bd")

    def test_03_get_current_user_me(self):
        """GET /api/auth/me with Bearer token returns authenticated student's profile."""
        user, token, headers = self.register_and_login(
            name="Sharafat Ali",
            email="sharafat2207045@stud.kuet.ac.bd",
        )
        resp = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["id"], user["id"])
        self.assertEqual(data["email"], "sharafat2207045@stud.kuet.ac.bd")
        self.assertEqual(data["dept"], "CSE")
        self.assertEqual(data["batch"], "22")
        self.assertEqual(data["roll"], "045")

    def test_04_get_current_user_alias(self):
        """GET /api/auth/current acts as an alias to /api/auth/me."""
        _, _, headers = self.register_and_login(
            name="Anik Sen",
            email="anik2103042@stud.kuet.ac.bd",
        )
        resp = self.client.get("/api/auth/current", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["name"], "Anik Sen")
        self.assertEqual(data["dept"], "EEE")

    def test_05_get_user_public_profile(self):
        """GET /api/auth/user/{id} returns public profile details for student identification."""
        user, _, _ = self.register_and_login(
            name="Sadia Afrin",
            email="sadia2201064@stud.kuet.ac.bd",
        )
        resp = self.client.get(f"/api/auth/user/{user['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["id"], user["id"])
        self.assertEqual(data["name"], "Sadia Afrin")
        self.assertEqual(data["dept"], "CE")
        self.assertEqual(data["karma"], 100)

    # =========================================================================
    # 2. Roll Decoding & Department Mapping (Features 2, 3)
    # =========================================================================

    def test_06_roll_decoding_cse(self):
        """Roll decoder correctly resolves department code 07 to CSE."""
        resp = self.register_user(
            name="CSE Student",
            email="student2107099@stud.kuet.ac.bd",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["batch"], "21")
        self.assertEqual(data["dept"], "CSE")
        self.assertEqual(data["roll"], "099")

    def test_07_roll_decoding_eee(self):
        """Roll decoder correctly resolves department code 03 to EEE."""
        resp = self.register_user(
            name="EEE Student",
            email="student2203015@stud.kuet.ac.bd",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["batch"], "22")
        self.assertEqual(data["dept"], "EEE")
        self.assertEqual(data["roll"], "015")

    def test_08_roll_decoding_ce(self):
        """Roll decoder correctly resolves department code 01 to CE."""
        resp = self.register_user(
            name="CE Student",
            email="student2001033@stud.kuet.ac.bd",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["batch"], "20")
        self.assertEqual(data["dept"], "CE")
        self.assertEqual(data["roll"], "033")

    def test_09_roll_decoding_me(self):
        """Roll decoder correctly resolves department code 05 to ME."""
        resp = self.register_user(
            name="ME Student",
            email="student2305088@stud.kuet.ac.bd",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["batch"], "23")
        self.assertEqual(data["dept"], "ME")
        self.assertEqual(data["roll"], "088")

    def test_10_roll_decoding_specialized_depts(self):
        """Roll decoder correctly maps specialized KUET departments (ECE=09, IEM=11, BME=15, MTE=25, LE=29)."""
        dept_cases = [
            ("student2209001@stud.kuet.ac.bd", "ECE"),
            ("student2111002@stud.kuet.ac.bd", "IEM"),
            ("student2315003@stud.kuet.ac.bd", "BME"),
            ("student2025004@stud.kuet.ac.bd", "MTE"),
            ("student2429005@stud.kuet.ac.bd", "LE"),
        ]
        for email, expected_dept in dept_cases:
            resp = self.register_user(name=f"Student {expected_dept}", email=email)
            self.assertEqual(resp.status_code, 200, f"Failed for email {email}: {resp.text}")
            self.assertEqual(resp.json()["dept"], expected_dept)

    # =========================================================================
    # 3. Item Listings & Demand Beacons (Feature 11)
    # =========================================================================

    def test_11_create_lend_item(self):
        """Create a lend item listing with title, specs, condition, zone, and coordinates."""
        _, _, headers = self.register_and_login(
            name="Lender",
            email="lender2107001@stud.kuet.ac.bd",
        )
        item = self.create_item(
            auth_headers=headers,
            title="Fluke 115 Multimeter",
            category="Electronics",
            item_type="lend",
            specs="CAT III 600V safety rated",
            condition="Excellent",
            zone="cse_bldg",
            latitude=22.9003,
            longitude=89.5024,
        )
        self.assertIsNotNone(item["id"])
        self.assertEqual(item["title"], "Fluke 115 Multimeter")
        self.assertEqual(item["type"], "lend")
        self.assertTrue(item["is_available"])

    def test_12_create_borrow_beacon(self):
        """Create a demand beacon with type='borrow' and status='beacon'."""
        _, _, headers = self.register_and_login(
            name="Requester",
            email="requester2307002@stud.kuet.ac.bd",
        )
        payload = {
            "title": "URGENT BEACON: MacBook 67W Charger",
            "category": "Electronics & Power",
            "type": "borrow",
            "specs": "Need USB-C PD charger for 2 hours",
            "condition": "N/A",
            "zone": "central_library",
            "status": "beacon",
        }
        resp = self.client.post("/api/items", json_data=payload, headers=headers)
        self.assertEqual(resp.status_code, 201)
        item = resp.json()["item"]
        self.assertEqual(item["type"], "borrow")
        self.assertEqual(item["status"], "beacon")

    def test_13_list_all_items(self):
        """GET /api/items returns list of available items."""
        _, _, headers = self.register_and_login(
            name="Student A",
            email="studenta2107011@stud.kuet.ac.bd",
        )
        self.create_item(auth_headers=headers, title="Casio 991CW Calculator")
        resp = self.client.get("/api/items")
        self.assertEqual(resp.status_code, 200)
        items = resp.json()
        self.assertGreaterEqual(len(items), 1)
        self.assertTrue(any(i["title"] == "Casio 991CW Calculator" for i in items))

    def test_14_get_item_by_id(self):
        """GET /api/items/{id} returns full item details including owner profile."""
        _, _, headers = self.register_and_login(
            name="Student B",
            email="studentb2107012@stud.kuet.ac.bd",
        )
        created = self.create_item(auth_headers=headers, title="Rigol DS1054Z Oscilloscope")
        resp = self.client.get(f"/api/items/{created['id']}")
        self.assertEqual(resp.status_code, 200)
        detail = resp.json()
        self.assertEqual(detail["id"], created["id"])
        self.assertEqual(detail["title"], "Rigol DS1054Z Oscilloscope")
        self.assertIn("owner", detail)
        self.assertEqual(detail["owner"]["dept"], "CSE")

    def test_15_update_and_delete_item(self):
        """Owner can update item details via PUT and delete listing via DELETE."""
        _, _, headers = self.register_and_login(
            name="Student C",
            email="studentc2107013@stud.kuet.ac.bd",
        )
        created = self.create_item(auth_headers=headers, title="Drafting Board")

        # Update
        update_payload = {
            "title": "Rotring A3 Drafting Board with T-Square",
            "category": "Drawing",
            "specs": "Magnetic clamp system",
        }
        put_resp = self.client.put(
            f"/api/items/{created['id']}",
            json_data=update_payload,
            headers=headers,
        )
        self.assertEqual(put_resp.status_code, 200)
        self.assertEqual(put_resp.json()["title"], "Rotring A3 Drafting Board with T-Square")

        # Delete
        del_resp = self.client.delete(f"/api/items/{created['id']}", headers=headers)
        self.assertEqual(del_resp.status_code, 200)

        # Confirm deleted
        get_resp = self.client.get(f"/api/items/{created['id']}")
        self.assertEqual(get_resp.status_code, 404)

    # =========================================================================
    # 4. Search & Filters (Feature 11)
    # =========================================================================

    def test_16_search_by_title_keyword(self):
        """Keyword search matches items across title text."""
        _, _, headers = self.register_and_login(
            name="Lender",
            email="lender2107021@stud.kuet.ac.bd",
        )
        self.create_item(auth_headers=headers, title="Arduino Uno R3 Microcontroller")
        resp = self.client.get("/api/items", params={"search": "Arduino"})
        self.assertEqual(resp.status_code, 200)
        results = resp.json()
        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(any("Arduino" in r["title"] for r in results))

    def test_17_search_by_hardware_specs(self):
        """Search term matches text embedded inside hardware specifications."""
        _, _, headers = self.register_and_login(
            name="Lender",
            email="lender2107022@stud.kuet.ac.bd",
        )
        self.create_item(
            auth_headers=headers,
            title="Development Board",
            specs="Features ATmega328P processor and 16MHz clock",
        )
        resp = self.client.get("/api/items", params={"search": "ATmega328P"})
        self.assertEqual(resp.status_code, 200)
        results = resp.json()
        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(any("ATmega328P" in r["specs"] for r in results))

    def test_18_filter_by_category(self):
        """Category filter returns only items matching the specified category."""
        _, _, headers = self.register_and_login(
            name="Lender",
            email="lender2107023@stud.kuet.ac.bd",
        )
        self.create_item(auth_headers=headers, title="Lab Coat", category="Apparel")
        self.create_item(auth_headers=headers, title="Textbook", category="Books")

        resp = self.client.get("/api/items", params={"category": "Books"})
        self.assertEqual(resp.status_code, 200)
        results = resp.json()
        self.assertTrue(all(r["category"].lower() == "books" for r in results))

    def test_19_filter_by_item_type(self):
        """Filter by type distinguishes between 'lend' listings and 'borrow' beacons."""
        _, _, headers = self.register_and_login(
            name="Lender",
            email="lender2107024@stud.kuet.ac.bd",
        )
        self.create_item(auth_headers=headers, title="Lending Breadboard", item_type="lend")
        self.create_item(auth_headers=headers, title="Seeking Multimeter", item_type="borrow")

        resp = self.client.get("/api/items", params={"type": "lend"})
        self.assertEqual(resp.status_code, 200)
        results = resp.json()
        self.assertTrue(all(r["type"] == "lend" for r in results))

    def test_20_filter_by_campus_zone(self):
        """Zone filter retrieves items located at a designated KUET campus landmark."""
        _, _, headers = self.register_and_login(
            name="Lender",
            email="lender2107025@stud.kuet.ac.bd",
        )
        self.create_item(auth_headers=headers, title="CSE Lab Manual", zone="cse_bldg")
        self.create_item(auth_headers=headers, title="EEE Lab Manual", zone="eee_bldg")

        resp = self.client.get("/api/items", params={"zone": "cse_bldg"})
        self.assertEqual(resp.status_code, 200)
        results = resp.json()
        self.assertTrue(all(r["zone"] == "cse_bldg" for r in results))

    # =========================================================================
    # 5. Borrow Requests Lifecycle (Feature 14)
    # =========================================================================

    def test_21_create_borrow_request(self):
        """Borrower creates request with duration, purpose, pickup zone; status is pending."""
        _, _, owner_headers = self.register_and_login(name="Owner", email="owner2107031@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_headers, title="Soldering Iron")

        _, _, borrower_headers = self.register_and_login(name="Borrower", email="borrower2307032@stud.kuet.ac.bd")
        resp = self.create_borrow_request(
            auth_headers=borrower_headers,
            item_id=item["id"],
            duration_hours=12,
            purpose="Hardware Project",
            pickup_zone="cse_bldg",
        )
        self.assertEqual(resp.status_code, 200)
        req = resp.json()
        self.assertEqual(req["status"], "pending")
        self.assertEqual(req["item_id"], item["id"])
        self.assertEqual(req["duration_hours"], 12)

    def test_22_get_my_requests(self):
        """GET /api/requests/me returns requests associated with the authenticated user."""
        _, _, owner_headers = self.register_and_login(name="Owner", email="owner2107033@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_headers, title="Logic Analyzer")

        _, _, borrower_headers = self.register_and_login(name="Borrower", email="borrower2307034@stud.kuet.ac.bd")
        self.create_borrow_request(auth_headers=borrower_headers, item_id=item["id"])

        resp = self.client.get("/api/requests/me", headers=borrower_headers)
        self.assertEqual(resp.status_code, 200)
        reqs = resp.json()
        self.assertGreaterEqual(len(reqs), 1)

    def test_23_owner_accept_borrow_request(self):
        """Owner accepts request: status transitions to 'accepted' and item becomes unavailable."""
        _, _, owner_headers = self.register_and_login(name="Owner", email="owner2107035@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_headers, title="Casio fx-991EX")

        _, _, borrower_headers = self.register_and_login(name="Borrower", email="borrower2307036@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_headers, item_id=item["id"]).json()

        accept_resp = self.client.put(
            f"/api/requests/{req['id']}/status",
            json_data={"status": "accepted"},
            headers=owner_headers,
        )
        self.assertEqual(accept_resp.status_code, 200)
        self.assertIn("accepted", accept_resp.json()["detail"].lower())

        # Verify item is no longer available
        item_check = self.client.get(f"/api/items/{item['id']}").json()
        self.assertFalse(item_check["is_available"])

    def test_24_owner_decline_borrow_request(self):
        """Owner declines request: status transitions to 'declined' and item remains available."""
        _, _, owner_headers = self.register_and_login(name="Owner", email="owner2107037@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_headers, title="Raspberry Pi 4")

        _, _, borrower_headers = self.register_and_login(name="Borrower", email="borrower2307038@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_headers, item_id=item["id"]).json()

        decline_resp = self.client.put(
            f"/api/requests/{req['id']}/status",
            json_data={"status": "declined"},
            headers=owner_headers,
        )
        self.assertEqual(decline_resp.status_code, 200)

        # Verify item remains available
        item_check = self.client.get(f"/api/items/{item['id']}").json()
        self.assertTrue(item_check["is_available"])

    def test_25_auto_decline_competing_requests(self):
        """Accepting one request auto-declines competing pending requests for the same item."""
        _, _, owner_headers = self.register_and_login(name="Owner", email="owner2107039@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_headers, title="High-Speed Op-Amp")

        _, _, borrower_b_headers = self.register_and_login(name="Student B", email="studentb2307040@stud.kuet.ac.bd")
        req_b = self.create_borrow_request(auth_headers=borrower_b_headers, item_id=item["id"]).json()

        _, _, borrower_c_headers = self.register_and_login(name="Student C", email="studentc2307041@stud.kuet.ac.bd")
        req_c = self.create_borrow_request(auth_headers=borrower_c_headers, item_id=item["id"]).json()

        # Owner accepts Student B's request
        self.client.put(
            f"/api/requests/{req_b['id']}/status",
            json_data={"status": "accepted"},
            headers=owner_headers,
        )

        # Verify Student C's request was auto-declined
        my_reqs_c = self.client.get("/api/requests/me", headers=borrower_c_headers).json()
        c_status = [r["status"] for r in my_reqs_c if r["id"] == req_c["id"]][0]
        self.assertEqual(c_status, "declined")

    # =========================================================================
    # 6. Physical Handover Verification (Feature 15)
    # =========================================================================

    def _setup_accepted_request(self, prefix="handover"):
        _, _, owner_h = self.register_and_login(name="Owner", email=f"{prefix}own2107051@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Lab Meter")
        _, _, borrower_h = self.register_and_login(name="Borrower", email=f"{prefix}bor2307052@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"]).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=owner_h)
        return req, owner_h, borrower_h

    def test_26_start_handover_generates_otp(self):
        """Owner starts transaction: generates 4-digit numeric OTP."""
        req, owner_h, _ = self._setup_accepted_request(prefix="otp")
        resp = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=owner_h)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("otp", data)
        self.assertEqual(len(data["otp"]), 4)
        self.assertTrue(data["otp"].isdigit())

    def test_27_start_handover_generates_qr_code(self):
        """Owner starts transaction: generates QR code base64 payload."""
        req, owner_h, _ = self._setup_accepted_request(prefix="qr")
        resp = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=owner_h)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("qr_code", data)
        self.assertTrue(data["qr_code"].startswith("data:image/png;base64,"))

    def test_28_verify_handover_with_valid_otp(self):
        """Borrower provides valid OTP to verify physical handover, moving status to 'borrowed'."""
        req, owner_h, borrower_h = self._setup_accepted_request(prefix="vfy")
        start_res = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=owner_h).json()
        otp = start_res["otp"]

        verify_res = self.client.post(
            "/api/transactions/verify",
            json_data={"request_id": req["id"], "otp": otp},
            headers=borrower_h,
        )
        self.assertEqual(verify_res.status_code, 200)
        self.assertIn("borrowed", verify_res.json()["detail"].lower())

    def test_29_handover_sets_borrowed_at_timestamp(self):
        """Verifying handover sets the borrowed_at UTC timestamp in the database."""
        req, owner_h, borrower_h = self._setup_accepted_request(prefix="ts")
        start_res = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=owner_h).json()
        self.client.post(
            "/api/transactions/verify",
            json_data={"request_id": req["id"], "otp": start_res["otp"]},
            headers=borrower_h,
        )
        trans = self.db.query(models.Transaction).filter(models.Transaction.request_id == req["id"]).first()
        self.assertIsNotNone(trans.borrowed_at)
        self.assertEqual(trans.status, "borrowed")

    def test_30_handover_clears_sensitive_otp(self):
        """Upon successful verification, the one-time OTP is cleared from the transaction record."""
        req, owner_h, borrower_h = self._setup_accepted_request(prefix="clr")
        start_res = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=owner_h).json()
        self.client.post(
            "/api/transactions/verify",
            json_data={"request_id": req["id"], "otp": start_res["otp"]},
            headers=borrower_h,
        )
        trans = self.db.query(models.Transaction).filter(models.Transaction.request_id == req["id"]).first()
        self.assertIsNone(trans.otp)
        self.assertIsNone(trans.qr_code)

    # =========================================================================
    # 7. Item Return & Karma Engine (Feature 16)
    # =========================================================================

    def _setup_borrowed_transaction(self, prefix="ret"):
        req, owner_h, borrower_h = self._setup_accepted_request(prefix=prefix)
        start_res = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=owner_h).json()
        self.client.post("/api/transactions/verify", json_data={"request_id": req["id"], "otp": start_res["otp"]}, headers=borrower_h)
        return req, owner_h, borrower_h

    def test_31_return_item_on_time_success(self):
        """Borrower confirms return: request is completed, transaction status is 'returned'."""
        req, _, borrower_h = self._setup_borrowed_transaction(prefix="ret1")
        resp = self.client.post(f"/api/transactions/return/{req['id']}", headers=borrower_h)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("karma_updated", data)
        self.assertTrue(data["karma_updated"]["is_on_time"])

    def test_32_return_restores_item_availability(self):
        """Returning an item restores item.is_available to True and status to 'available'."""
        req, _, borrower_h = self._setup_borrowed_transaction(prefix="ret2")
        self.client.post(f"/api/transactions/return/{req['id']}", headers=borrower_h)
        item = self.client.get(f"/api/items/{req['item_id']}").json()
        self.assertTrue(item["is_available"])
        self.assertEqual(item["status"], "available")

    def test_33_on_time_karma_award_lender(self):
        """Lender receives +10 Karma points upon on-time return."""
        owner_user, _, owner_h = self.register_and_login(name="Lender", email="lender2107061@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Casio fx-991CW")
        _, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307062@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"], duration_hours=24).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=owner_h)
        start = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=owner_h).json()
        self.client.post("/api/transactions/verify", json_data={"request_id": req["id"], "otp": start["otp"]}, headers=borrower_h)

        self.client.post(f"/api/transactions/return/{req['id']}", headers=borrower_h)
        owner_prof = self.client.get("/api/auth/me", headers=owner_h).json()
        self.assertEqual(owner_prof["karma"], owner_user["karma"] + 10)
        self.assertEqual(owner_prof["total_lends"], 1)

    def test_34_on_time_karma_award_borrower(self):
        """Borrower receives +5 Karma points upon on-time return."""
        _, _, owner_h = self.register_and_login(name="Lender", email="lender2107063@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Logic Probe")
        borrower_user, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307064@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"], duration_hours=24).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=owner_h)
        start = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=owner_h).json()
        self.client.post("/api/transactions/verify", json_data={"request_id": req["id"], "otp": start["otp"]}, headers=borrower_h)

        self.client.post(f"/api/transactions/return/{req['id']}", headers=borrower_h)
        borrower_prof = self.client.get("/api/auth/me", headers=borrower_h).json()
        self.assertEqual(borrower_prof["karma"], borrower_user["karma"] + 5)
        self.assertEqual(borrower_prof["total_borrows"], 1)

    def test_35_late_return_karma_penalty_borrower(self):
        """Late return penalizes borrower -30 Karma points while awarding lender +10."""
        _, _, owner_h = self.register_and_login(name="Lender", email="lender2107065@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Vernier Caliper")
        borrower_user, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307066@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"], duration_hours=2).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=owner_h)
        start = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=owner_h).json()
        self.client.post("/api/transactions/verify", json_data={"request_id": req["id"], "otp": start["otp"]}, headers=borrower_h)

        # Simulate time passing beyond duration
        trans = self.db.query(models.Transaction).filter(models.Transaction.request_id == req["id"]).first()
        trans.borrowed_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=5)
        self.db.commit()

        ret_resp = self.client.post(f"/api/transactions/return/{req['id']}", headers=borrower_h)
        self.assertEqual(ret_resp.status_code, 200)
        karma_data = ret_resp.json()["karma_updated"]
        self.assertFalse(karma_data["is_on_time"])
        self.assertEqual(karma_data["borrower_change"], -30)
        self.assertEqual(karma_data["owner_gain"], 10)

        borrower_prof = self.client.get("/api/auth/me", headers=borrower_h).json()
        self.assertEqual(borrower_prof["karma"], borrower_user["karma"] - 30)

    # =========================================================================
    # 8. Messaging & Conversations (Feature 17)
    # =========================================================================

    def test_36_send_direct_message(self):
        """Student B sends direct 1:1 message to Student A."""
        user_a, _, _ = self.register_and_login(name="Student A", email="studanta2107071@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Student B", email="studantb2307072@stud.kuet.ac.bd")

        resp = self.client.post(
            f"/api/chat/direct/{user_a['id']}",
            json_data={"content": "Hi! Is your oscilloscope available today?"},
            headers=headers_b,
        )
        self.assertEqual(resp.status_code, 200)
        msg = resp.json()
        self.assertEqual(msg["content"], "Hi! Is your oscilloscope available today?")
        self.assertEqual(msg["recipient_id"], user_a["id"])

    def test_37_list_conversations_inbox(self):
        """Student A sees incoming conversation in inbox with unread_count >= 1."""
        user_a, _, headers_a = self.register_and_login(name="Student A", email="studanta2107073@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Student B", email="studantb2307074@stud.kuet.ac.bd")

        self.client.post(
            f"/api/chat/direct/{user_a['id']}",
            json_data={"content": "Can I borrow your book tomorrow?"},
            headers=headers_b,
        )

        resp = self.client.get("/api/chat/conversations", headers=headers_a)
        self.assertEqual(resp.status_code, 200)
        convos = resp.json()
        self.assertEqual(len(convos), 1)
        self.assertEqual(convos[0]["unread_count"], 1)

    def test_38_get_direct_messages_marks_read(self):
        """Opening a direct message thread marks incoming messages read and resets unread count."""
        user_a, _, headers_a = self.register_and_login(name="Student A", email="studanta2107075@stud.kuet.ac.bd")
        user_b, _, headers_b = self.register_and_login(name="Student B", email="studantb2307076@stud.kuet.ac.bd")

        self.client.post(
            f"/api/chat/direct/{user_a['id']}",
            json_data={"content": "Let's meet at Central Library."},
            headers=headers_b,
        )

        # Student A opens direct thread
        resp = self.client.get(f"/api/chat/direct/{user_b['id']}", headers=headers_a)
        self.assertEqual(resp.status_code, 200)
        messages = resp.json()
        self.assertGreaterEqual(len(messages), 1)

        # Re-check conversations inbox
        convos = self.client.get("/api/chat/conversations", headers=headers_a).json()
        self.assertEqual(convos[0]["unread_count"], 0)

    def test_39_bidirectional_chat_thread(self):
        """Two students can exchange back-and-forth messages in the same conversation."""
        user_a, _, headers_a = self.register_and_login(name="Student A", email="studanta2107077@stud.kuet.ac.bd")
        user_b, _, headers_b = self.register_and_login(name="Student B", email="studantb2307078@stud.kuet.ac.bd")

        self.client.post(f"/api/chat/direct/{user_a['id']}", json_data={"content": "Hello A!"}, headers=headers_b)
        self.client.post(f"/api/chat/direct/{user_b['id']}", json_data={"content": "Hello B!"}, headers=headers_a)

        thread = self.client.get(f"/api/chat/direct/{user_b['id']}", headers=headers_a).json()
        self.assertEqual(len(thread), 2)
        self.assertEqual(thread[0]["content"], "Hello A!")
        self.assertEqual(thread[1]["content"], "Hello B!")

    def test_40_request_linked_messages(self):
        """Students can exchange chat messages linked to a specific borrow request ID."""
        req, owner_h, borrower_h = self._setup_accepted_request(prefix="chatreq")
        msg_resp = self.client.post(
            f"/api/chat/{req['id']}/messages",
            json_data={"content": "Ready for pickup at CSE building."},
            headers=owner_h,
        )
        self.assertEqual(msg_resp.status_code, 200)

        get_resp = self.client.get(f"/api/chat/{req['id']}/messages", headers=borrower_h)
        self.assertEqual(get_resp.status_code, 200)
        messages = get_resp.json()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["content"], "Ready for pickup at CSE building.")

    # =========================================================================
    # 9. In-App Notifications (Feature 18)
    # =========================================================================

    def test_41_list_student_notifications(self):
        """GET /api/notifications returns student notification feed."""
        _, _, headers = self.register_and_login(name="Student", email="student2107081@stud.kuet.ac.bd")
        resp = self.client.get("/api/notifications", headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    def test_42_direct_chat_generates_notification(self):
        """Sending a direct chat message automatically triggers a notification for the recipient."""
        user_a, _, headers_a = self.register_and_login(name="Student A", email="studanta2107082@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Student B", email="studantb2307083@stud.kuet.ac.bd")

        self.client.post(
            f"/api/chat/direct/{user_a['id']}",
            json_data={"content": "Important notification test"},
            headers=headers_b,
        )

        notifs = self.client.get("/api/notifications", headers=headers_a).json()
        self.assertGreaterEqual(len(notifs), 1)
        self.assertIn("Student B", notifs[0]["title"])

    def test_43_review_generates_notification(self):
        """Submitting a peer review generates a notification for the reviewee."""
        user_a, _, headers_a = self.register_and_login(name="Student A", email="studanta2107084@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Student B", email="studantb2307085@stud.kuet.ac.bd")

        self.client.post(
            "/api/reviews",
            json_data={"reviewee_id": user_a["id"], "rating": 5, "comment": "Great lender!"},
            headers=headers_b,
        )

        notifs = self.client.get("/api/notifications", headers=headers_a).json()
        self.assertGreaterEqual(len(notifs), 1)
        self.assertIn("review", notifs[0]["title"].lower())

    def test_44_mark_single_notification_read(self):
        """PUT /api/notifications/{id}/read marks a notification as read."""
        user_a, _, headers_a = self.register_and_login(name="Student A", email="studanta2107086@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Student B", email="studantb2307087@stud.kuet.ac.bd")

        self.client.post(f"/api/chat/direct/{user_a['id']}", json_data={"content": "Read me!"}, headers=headers_b)
        notifs = self.client.get("/api/notifications", headers=headers_a).json()
        notif_id = notifs[0]["id"]
        self.assertFalse(notifs[0]["is_read"])

        res = self.client.put(f"/api/notifications/{notif_id}/read", headers=headers_a)
        self.assertEqual(res.status_code, 200)

        updated_notifs = self.client.get("/api/notifications", headers=headers_a).json()
        self.assertTrue(updated_notifs[0]["is_read"])

    def test_45_mark_all_notifications_read(self):
        """PUT /api/notifications/read-all marks all unread notifications as read."""
        user_a, _, headers_a = self.register_and_login(name="Student A", email="studanta2107088@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Student B", email="studantb2307089@stud.kuet.ac.bd")

        self.client.post(f"/api/chat/direct/{user_a['id']}", json_data={"content": "Msg 1"}, headers=headers_b)
        self.client.post(f"/api/chat/direct/{user_a['id']}", json_data={"content": "Msg 2"}, headers=headers_b)

        res = self.client.put("/api/notifications/read-all", headers=headers_a)
        self.assertEqual(res.status_code, 200)

        notifs = self.client.get("/api/notifications", headers=headers_a).json()
        self.assertTrue(all(n["is_read"] for n in notifs))

    # =========================================================================
    # 10. Peer Reviews & Ratings (Feature 19)
    # =========================================================================

    def test_46_submit_valid_peer_review(self):
        """Student B submits 5-star review for Student A with feedback comment."""
        user_a, _, _ = self.register_and_login(name="Student A", email="studanta2107091@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Student B", email="studantb2307092@stud.kuet.ac.bd")

        resp = self.client.post(
            "/api/reviews",
            json_data={
                "reviewee_id": user_a["id"],
                "rating": 5,
                "comment": "Punctual and item was in pristine condition!",
            },
            headers=headers_b,
        )
        self.assertEqual(resp.status_code, 200)
        review = resp.json()
        self.assertEqual(review["rating"], 5)
        self.assertEqual(review["reviewee_id"], user_a["id"])

    def test_47_get_user_reviews_list(self):
        """GET /api/reviews/user/{id} retrieves list of reviews for that user."""
        user_a, _, _ = self.register_and_login(name="Student A", email="studanta2107093@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Student B", email="studantb2307094@stud.kuet.ac.bd")

        self.client.post(
            "/api/reviews",
            json_data={"reviewee_id": user_a["id"], "rating": 4, "comment": "Good borrower."},
            headers=headers_b,
        )

        resp = self.client.get(f"/api/reviews/user/{user_a['id']}")
        self.assertEqual(resp.status_code, 200)
        reviews = resp.json()
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["comment"], "Good borrower.")

    def test_48_review_includes_reviewer_profile(self):
        """Review object includes reviewer profile information."""
        user_a, _, _ = self.register_and_login(name="Student A", email="studanta2107095@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Reviewer Bob", email="bobby2307096@stud.kuet.ac.bd")

        self.client.post(
            "/api/reviews",
            json_data={"reviewee_id": user_a["id"], "rating": 5, "comment": "Great!"},
            headers=headers_b,
        )

        reviews = self.client.get(f"/api/reviews/user/{user_a['id']}").json()
        self.assertIn("reviewer", reviews[0])
        self.assertEqual(reviews[0]["reviewer"]["name"], "Reviewer Bob")

    def test_49_rating_value_bounds(self):
        """Ratings accept valid integers between 1 and 5."""
        user_a, _, _ = self.register_and_login(name="Student A", email="studanta2107097@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Student B", email="studantb2307098@stud.kuet.ac.bd")

        for rating in (1, 3, 5):
            resp = self.client.post(
                "/api/reviews",
                json_data={"reviewee_id": user_a["id"], "rating": rating, "comment": f"Rating {rating}"},
                headers=headers_b,
            )
            self.assertEqual(resp.status_code, 200)

    def test_50_multiple_reviews_chronological(self):
        """Multiple reviews are returned in descending chronological order."""
        user_a, _, _ = self.register_and_login(name="Student A", email="studanta2107099@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Student B", email="studantb2307100@stud.kuet.ac.bd")
        _, _, headers_c = self.register_and_login(name="Student C", email="studantc2307101@stud.kuet.ac.bd")

        self.client.post("/api/reviews", json_data={"reviewee_id": user_a["id"], "rating": 4, "comment": "First review"}, headers=headers_b)
        self.client.post("/api/reviews", json_data={"reviewee_id": user_a["id"], "rating": 5, "comment": "Second review"}, headers=headers_c)

        reviews = self.client.get(f"/api/reviews/user/{user_a['id']}").json()
        self.assertEqual(len(reviews), 2)
        self.assertEqual(reviews[0]["comment"], "Second review")
        self.assertEqual(reviews[1]["comment"], "First review")

    # =========================================================================
    # 11. Campus Landmarks & Coordinates (Feature 12)
    # =========================================================================

    def test_51_get_landmarks_endpoint(self):
        """GET /api/landmarks returns status 200 with success=True."""
        resp = self.client.get("/api/landmarks")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])

    def test_52_campus_center_coordinates(self):
        """Landmarks API provides official KUET campus center [22.9006, 89.5024]."""
        resp = self.client.get("/api/landmarks")
        campus = resp.json().get("campus", {})
        self.assertEqual(campus.get("center"), [22.9006, 89.5024])

    def test_53_campus_perimeter_radius(self):
        """Landmarks API defines campus boundary radius as 700 meters."""
        resp = self.client.get("/api/landmarks")
        campus = resp.json().get("campus", {})
        self.assertEqual(campus.get("boundary_radius_meters"), 700)

    def test_54_campus_zones_coverage(self):
        """Landmarks response contains at least 21 campus zones across KUET."""
        resp = self.client.get("/api/landmarks")
        zones = resp.json().get("zones", [])
        self.assertGreaterEqual(len(zones), 21)

    def test_55_zone_coordinate_bounds(self):
        """All campus zones have valid coordinates within KUET geographic boundary."""
        resp = self.client.get("/api/landmarks")
        zones = resp.json().get("zones", [])
        for z in zones:
            self.assertIn("coords", z)
            lat, lng = z["coords"]
            self.assertTrue(22.88 <= lat <= 22.92, f"Zone {z['id']} lat {lat} out of bounds")
            self.assertTrue(89.48 <= lng <= 89.52, f"Zone {z['id']} lng {lng} out of bounds")
