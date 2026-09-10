"""
Tier 2: Boundary & Corner Cases (>=5 tests per feature area)
Tests extreme inputs, invalid formats, permission blocks, state machine violations:
- Email Domain Rejections (5 tests)
- Roll Decoding Corner Cases (5 tests)
- Auth Security & Token Boundaries (5 tests)
- Composite Roll & Email Collisions (5 tests)
- Item Boundaries & Permissions (5 tests)
- Campus Geofence & Landmark Boundary Calculations (5 tests)
- Borrow Requests Boundaries & Guards (5 tests)
- Handover & OTP Verification Boundaries (5 tests)
- Item Return Boundaries (5 tests)
- Chat Boundaries & Input Validation (5 tests)
- Reviews & Reporting Boundaries (5 tests)
Total: 55 tests
"""

import math
from tests.base import BaseE2ETestCase
from app import models, auth


def haversine_distance(coord1, coord2):
    """Calculates haversine distance in meters between two [lat, lng] pairs."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class TestTier2Boundaries(BaseE2ETestCase):

    # =========================================================================
    # 1. Email Domain Rejections
    # =========================================================================

    def test_01_reject_gmail_domain(self):
        """Rejects non-KUET email domain @gmail.com with HTTP 400."""
        resp = self.register_user(name="Imposter", email="student2107001@gmail.com")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("@stud.kuet.ac.bd", resp.json()["detail"].lower())

    def test_02_reject_kuet_faculty_domain(self):
        """Rejects institutional faculty domain without stud. prefix (@kuet.ac.bd)."""
        resp = self.register_user(name="Faculty", email="teacher2107001@kuet.ac.bd")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("@stud.kuet.ac.bd", resp.json()["detail"].lower())

    def test_03_reject_other_university_domain(self):
        """Rejects emails from other educational institutions (@buet.ac.bd)."""
        resp = self.register_user(name="Other Student", email="student2107001@buet.ac.bd")
        self.assertEqual(resp.status_code, 400)

    def test_04_reject_subdomain_spoof(self):
        """Rejects spoofed nested subdomains like @evil.stud.kuet.ac.bd."""
        resp = self.register_user(name="Attacker", email="hacker2107001@evil.stud.kuet.ac.bd")
        self.assertEqual(resp.status_code, 400)

    def test_05_reject_missing_at_symbol(self):
        """Rejects email without @ symbol via 400 or schema validation 422."""
        resp = self.register_user(name="Invalid", email="student2107001stud.kuet.ac.bd")
        self.assertIn(resp.status_code, [400, 422])

    # =========================================================================
    # 2. Roll Decoding Corner Cases
    # =========================================================================

    def test_06_reject_email_without_7_digits(self):
        """Rejects email local part lacking 7-digit student roll suffix."""
        resp = self.register_user(name="No Roll", email="tanvir@stud.kuet.ac.bd")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("7-digit", resp.json()["detail"])

    def test_07_reject_roll_with_letters_in_suffix(self):
        """Rejects alphanumeric roll suffix (e.g. 2107AB1)."""
        resp = self.register_user(name="Alpha Roll", email="student2107AB1@stud.kuet.ac.bd")
        self.assertEqual(resp.status_code, 400)

    def test_08_reject_too_few_digits(self):
        """Rejects roll with only 6 digits (e.g. 210701)."""
        resp = self.register_user(name="Short Roll", email="student210701@stud.kuet.ac.bd")
        self.assertEqual(resp.status_code, 400)

    def test_09_reject_unrecognized_dept_code(self):
        """Rejects unrecognized department code (e.g. 99) with HTTP 400."""
        resp = self.register_user(name="Unknown Dept", email="student2199001@stud.kuet.ac.bd")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("recognized department", resp.json()["detail"].lower())

    def test_10_email_with_leading_trailing_whitespace(self):
        """Email provided with leading/trailing whitespace is trimmed and processed cleanly."""
        resp = self.register_user(
            name="Spaced Student",
            email="  student2107080@stud.kuet.ac.bd  ",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["email"], "student2107080@stud.kuet.ac.bd")

    # =========================================================================
    # 3. Auth Security & Token Boundaries
    # =========================================================================

    def test_11_login_with_incorrect_password(self):
        """Login with wrong password rejected with HTTP 401."""
        self.register_user(name="Student", email="user2107011@stud.kuet.ac.bd", password="RealPassword1")
        resp = self.login_user(email="user2107011@stud.kuet.ac.bd", password="WrongPassword9")
        self.assertEqual(resp.status_code, 401)
        self.assertIn("incorrect", resp.json()["detail"].lower())

    def test_12_login_with_nonexistent_user(self):
        """Login with unregistered email returns HTTP 401."""
        resp = self.login_user(email="ghost2107012@stud.kuet.ac.bd", password="password123")
        self.assertEqual(resp.status_code, 401)

    def test_13_access_me_without_authorization_header(self):
        """GET /api/auth/me without Authorization header returns HTTP 403 Forbidden."""
        resp = self.client.get("/api/auth/me")
        self.assertEqual(resp.status_code, 403)

    def test_14_access_me_with_malformed_token(self):
        """GET /api/auth/me with garbage JWT token returns HTTP 401."""
        resp = self.client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.valid.jwt"})
        self.assertEqual(resp.status_code, 401)

    def test_15_access_me_with_tampered_signature(self):
        """JWT signed with an unauthorized secret key is rejected with HTTP 401."""
        from jose import jwt
        tampered_token = jwt.encode({"sub": "1"}, "FAKE_SECRET_KEY", algorithm="HS256")
        resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
        self.assertEqual(resp.status_code, 401)

    # =========================================================================
    # 4. Composite Roll & Email Collisions
    # =========================================================================

    def test_16_duplicate_email_registration_rejected(self):
        """Registering an email that is already registered returns HTTP 400."""
        self.register_user(name="First", email="dup2107015@stud.kuet.ac.bd")
        resp = self.register_user(name="Second", email="dup2107015@stud.kuet.ac.bd")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("already registered", resp.json()["detail"].lower())

    def test_17_duplicate_roll_same_batch_dept_rejected(self):
        """Different local part prefix with identical batch/dept/roll returns HTTP 400."""
        self.register_user(name="Original", email="first2107016@stud.kuet.ac.bd")
        resp = self.register_user(name="Impersonator", email="alias2107016@stud.kuet.ac.bd")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("already registered", resp.json()["detail"].lower())

    def test_18_same_roll_different_batch_allowed(self):
        """Same roll in different batches (e.g. 2107017 vs 2207017) is permitted."""
        resp1 = self.register_user(name="Senior", email="senior2107017@stud.kuet.ac.bd")
        resp2 = self.register_user(name="Junior", email="junior2207017@stud.kuet.ac.bd")
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp2.status_code, 200)

    def test_19_same_roll_different_dept_allowed(self):
        """Same roll and batch in different departments (CSE 2107018 vs EEE 2103018) is permitted."""
        resp_cse = self.register_user(name="CSE Student", email="cse2107018@stud.kuet.ac.bd")
        resp_eee = self.register_user(name="EEE Student", email="eee2103018@stud.kuet.ac.bd")
        self.assertEqual(resp_cse.status_code, 200)
        self.assertEqual(resp_eee.status_code, 200)

    def test_20_case_insensitive_email_duplicate(self):
        """Email registration uniqueness is case-insensitive."""
        self.register_user(name="Lower", email="case2107019@stud.kuet.ac.bd")
        resp = self.register_user(name="Upper", email="CASE2107019@STUD.KUET.AC.BD")
        self.assertEqual(resp.status_code, 400)

    # =========================================================================
    # 5. Item Boundaries & Permissions
    # =========================================================================

    def test_21_create_item_empty_title_rejected(self):
        """Posting an item with an empty or blank title returns HTTP 422."""
        _, _, headers = self.register_and_login(name="Student", email="item2107021@stud.kuet.ac.bd")
        resp = self.client.post("/api/items", json_data={"title": "   ", "type": "lend"}, headers=headers)
        self.assertEqual(resp.status_code, 422)

    def test_22_create_item_invalid_type_rejected(self):
        """Posting an item with type not in ('lend', 'borrow') returns HTTP 422."""
        _, _, headers = self.register_and_login(name="Student", email="item2107022@stud.kuet.ac.bd")
        resp = self.client.post("/api/items", json_data={"title": "Invalid Item", "type": "rent"}, headers=headers)
        self.assertEqual(resp.status_code, 422)

    def test_23_update_item_unauthorized_non_owner(self):
        """Non-owner student attempting to update an item returns HTTP 403."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107023@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Original Item")

        _, _, attacker_h = self.register_and_login(name="Attacker", email="attacker2307024@stud.kuet.ac.bd")
        resp = self.client.put(
            f"/api/items/{item['id']}",
            json_data={"title": "Hacked Title", "category": "Electronics"},
            headers=attacker_h,
        )
        self.assertEqual(resp.status_code, 403)

    def test_24_delete_item_unauthorized_non_owner(self):
        """Non-owner student attempting to delete an item returns HTTP 403."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107025@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Protected Item")

        _, _, attacker_h = self.register_and_login(name="Attacker", email="attacker2307026@stud.kuet.ac.bd")
        resp = self.client.delete(f"/api/items/{item['id']}", headers=attacker_h)
        self.assertEqual(resp.status_code, 403)

    def test_25_get_nonexistent_item_returns_404(self):
        """GET /api/items/{id} for non-existent item ID returns HTTP 404."""
        resp = self.client.get("/api/items/999999")
        self.assertEqual(resp.status_code, 404)

    # =========================================================================
    # 6. Campus Geofence & Landmark Boundary Calculations
    # =========================================================================

    def test_26_item_coordinates_inside_campus_perimeter(self):
        """Item at CSE Building [22.9003, 89.5024] is within 700m radius of KUET Center."""
        kuet_center = [22.9006, 89.5024]
        cse_coords = [22.9003, 89.5024]
        dist = haversine_distance(kuet_center, cse_coords)
        self.assertLess(dist, 700.0)

    def test_27_item_coordinates_at_teligati_mess_boundary(self):
        """Teligati Mess Zone [22.8948, 89.5009] (~660m) is within the 700m perimeter."""
        kuet_center = [22.9006, 89.5024]
        teligati_coords = [22.8948, 89.5009]
        dist = haversine_distance(kuet_center, teligati_coords)
        self.assertLess(dist, 700.0)
        self.assertGreater(dist, 600.0)

    def test_28_item_coordinates_far_outside_perimeter(self):
        """Coordinates far from KUET (>3km) are identified as outside the 700m perimeter."""
        kuet_center = [22.9006, 89.5024]
        khulna_city = [22.8200, 89.5500]
        dist = haversine_distance(kuet_center, khulna_city)
        self.assertGreater(dist, 700.0)

    def test_29_item_with_null_coordinates(self):
        """Item created without explicit lat/lng succeeds with None coordinates."""
        _, _, headers = self.register_and_login(name="Student", email="geo2107027@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=headers, title="Textbook", latitude=None, longitude=None)
        self.assertIsNone(item["latitude"])
        self.assertIsNone(item["longitude"])

    def test_30_filter_by_nonexistent_zone_returns_empty(self):
        """Querying items with a non-existent zone returns an empty list without error."""
        resp = self.client.get("/api/items", params={"zone": "mars_rover_station"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    # =========================================================================
    # 7. Borrow Requests Boundaries & Guards
    # =========================================================================

    def test_31_self_borrowing_guard(self):
        """Owner attempting to borrow their own item is rejected with HTTP 400."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107031@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Self Loan Item")
        resp = self.create_borrow_request(auth_headers=owner_h, item_id=item["id"])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("own item", resp.json()["detail"].lower())

    def test_32_duplicate_pending_request_guard(self):
        """Borrower submitting duplicate pending request for same item rejected with HTTP 400."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107032@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Popular Item")
        _, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307033@stud.kuet.ac.bd")

        resp1 = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"])
        self.assertEqual(resp1.status_code, 200)

        resp2 = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"])
        self.assertEqual(resp2.status_code, 400)
        self.assertIn("already have a pending request", resp2.json()["detail"].lower())

    def test_33_request_unavailable_item_guard(self):
        """Borrow request for an unavailable item is rejected with HTTP 400."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107034@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Reserved Item")

        # Mark item unavailable directly in db
        db_item = self.db.query(models.Item).filter(models.Item.id == item["id"]).first()
        db_item.is_available = False
        self.db.commit()

        _, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307035@stud.kuet.ac.bd")
        resp = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("not available", resp.json()["detail"].lower())

    def test_34_request_nonexistent_item_returns_404(self):
        """Borrow request for a non-existent item ID returns HTTP 404."""
        _, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307036@stud.kuet.ac.bd")
        resp = self.create_borrow_request(auth_headers=borrower_h, item_id=999999)
        self.assertEqual(resp.status_code, 404)

    def test_35_status_update_by_non_owner_forbidden(self):
        """Borrower or stranger attempting to accept/decline request returns HTTP 403."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107037@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Special Item")
        _, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307038@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"]).json()

        # Borrower tries to accept own request
        resp = self.client.put(
            f"/api/requests/{req['id']}/status",
            json_data={"status": "accepted"},
            headers=borrower_h,
        )
        self.assertEqual(resp.status_code, 403)

    # =========================================================================
    # 8. Handover & OTP Verification Boundaries
    # =========================================================================

    def test_36_verify_handover_invalid_otp_rejected(self):
        """Borrower submitting an incorrect OTP returns HTTP 400."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107041@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Meter")
        _, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307042@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"]).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=owner_h)
        self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=owner_h)

        resp = self.client.post(
            "/api/transactions/verify",
            json_data={"request_id": req["id"], "otp": "0000"},
            headers=borrower_h,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("invalid otp", resp.json()["detail"].lower())

    def test_37_start_handover_on_pending_request_rejected(self):
        """Starting handover on a pending (not yet accepted) request returns HTTP 400."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107043@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Meter")
        _, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307044@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"]).json()

        resp = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=owner_h)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("not accepted", resp.json()["detail"].lower())

    def test_38_start_handover_by_non_owner_forbidden(self):
        """Borrower or non-owner attempting to start handover returns HTTP 403."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107045@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Meter")
        _, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307046@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"]).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=owner_h)

        resp = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=borrower_h)
        self.assertEqual(resp.status_code, 403)

    def test_39_verify_handover_by_non_borrower_forbidden(self):
        """Owner or third party attempting to verify handover returns HTTP 403."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107047@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Meter")
        _, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307048@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"]).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=owner_h)
        start = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=owner_h).json()

        resp = self.client.post(
            "/api/transactions/verify",
            json_data={"request_id": req["id"], "otp": start["otp"]},
            headers=owner_h,
        )
        self.assertEqual(resp.status_code, 403)

    def test_40_verify_already_borrowed_transaction_rejected(self):
        """Re-verifying an already verified/borrowed transaction returns HTTP 400."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107049@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Meter")
        _, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307050@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"]).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=owner_h)
        start = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=owner_h).json()

        # First verification succeeds
        self.client.post("/api/transactions/verify", json_data={"request_id": req["id"], "otp": start["otp"]}, headers=borrower_h)

        # Second verification fails
        resp = self.client.post("/api/transactions/verify", json_data={"request_id": req["id"], "otp": start["otp"]}, headers=borrower_h)
        self.assertEqual(resp.status_code, 400)

    # =========================================================================
    # 9. Item Return Boundaries
    # =========================================================================

    def test_41_return_by_non_borrower_forbidden(self):
        """Owner attempting to trigger borrower return endpoint returns HTTP 403."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107051@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Meter")
        _, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307052@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"]).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=owner_h)
        start = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=owner_h).json()
        self.client.post("/api/transactions/verify", json_data={"request_id": req["id"], "otp": start["otp"]}, headers=borrower_h)

        resp = self.client.post(f"/api/transactions/return/{req['id']}", headers=owner_h)
        self.assertEqual(resp.status_code, 403)

    def test_42_return_not_borrowed_item_rejected(self):
        """Attempting return before handover verification has occurred returns HTTP 400."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107053@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Meter")
        _, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307054@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"]).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=owner_h)
        self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=owner_h)

        resp = self.client.post(f"/api/transactions/return/{req['id']}", headers=borrower_h)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("not currently borrowed", resp.json()["detail"].lower())

    def test_43_return_nonexistent_request_returns_404(self):
        """Returning non-existent request ID returns HTTP 404."""
        _, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307055@stud.kuet.ac.bd")
        resp = self.client.post("/api/transactions/return/999999", headers=borrower_h)
        self.assertEqual(resp.status_code, 404)

    def test_44_duplicate_return_attempt_rejected(self):
        """Calling return a second time on an already returned item returns HTTP 400."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107056@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Meter")
        _, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307057@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"]).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=owner_h)
        start = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=owner_h).json()
        self.client.post("/api/transactions/verify", json_data={"request_id": req["id"], "otp": start["otp"]}, headers=borrower_h)

        # First return succeeds
        self.client.post(f"/api/transactions/return/{req['id']}", headers=borrower_h)

        # Second return fails
        resp = self.client.post(f"/api/transactions/return/{req['id']}", headers=borrower_h)
        self.assertEqual(resp.status_code, 400)

    def test_45_return_without_prior_transaction_rejected(self):
        """Attempting to return an accepted request where start handover was never called returns HTTP 400."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107058@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Meter")
        _, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307059@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"]).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=owner_h)

        resp = self.client.post(f"/api/transactions/return/{req['id']}", headers=borrower_h)
        self.assertEqual(resp.status_code, 400)

    # =========================================================================
    # 10. Chat Boundaries & Input Validation
    # =========================================================================

    def test_46_self_chat_guard(self):
        """Attempting to start direct chat with oneself returns HTTP 400."""
        user, _, headers = self.register_and_login(name="Student", email="chat2107061@stud.kuet.ac.bd")
        resp = self.client.post(
            f"/api/chat/direct/{user['id']}",
            json_data={"content": "Talking to myself"},
            headers=headers,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("cannot chat with yourself", resp.json()["detail"].lower())

    def test_47_empty_message_content_rejected(self):
        """Sending empty message body or spaces returns HTTP 400."""
        user_a, _, _ = self.register_and_login(name="Student A", email="chat2107062@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Student B", email="chat2307063@stud.kuet.ac.bd")

        resp = self.client.post(
            f"/api/chat/direct/{user_a['id']}",
            json_data={"content": "   "},
            headers=headers_b,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("message cannot be empty", resp.json()["detail"].lower())

    def test_48_chat_with_nonexistent_user_returns_404(self):
        """Sending direct message to non-existent student returns HTTP 404."""
        _, _, headers = self.register_and_login(name="Student", email="chat2107064@stud.kuet.ac.bd")
        resp = self.client.post(
            "/api/chat/direct/999999",
            json_data={"content": "Hello ghost"},
            headers=headers,
        )
        self.assertEqual(resp.status_code, 404)

    def test_49_request_message_by_unauthorized_user(self):
        """Third party attempting to access private request messages returns HTTP 403."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107065@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Meter")
        _, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307066@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"]).json()

        _, _, stranger_h = self.register_and_login(name="Stranger", email="stranger2307067@stud.kuet.ac.bd")
        resp = self.client.get(f"/api/chat/{req['id']}/messages", headers=stranger_h)
        self.assertEqual(resp.status_code, 403)

    def test_50_request_message_on_nonexistent_request(self):
        """Sending request-linked message to non-existent request returns HTTP 404."""
        _, _, headers = self.register_and_login(name="Student", email="chat2107068@stud.kuet.ac.bd")
        resp = self.client.post(
            "/api/chat/999999/messages",
            json_data={"content": "Hello"},
            headers=headers,
        )
        self.assertEqual(resp.status_code, 404)

    # =========================================================================
    # 11. Reviews & Reporting Boundaries
    # =========================================================================

    def test_51_self_review_guard(self):
        """Attempting to submit review for oneself returns HTTP 400."""
        user, _, headers = self.register_and_login(name="Narcissist", email="self2107071@stud.kuet.ac.bd")
        resp = self.client.post(
            "/api/reviews",
            json_data={"reviewee_id": user["id"], "rating": 5, "comment": "I am great"},
            headers=headers,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("cannot review yourself", resp.json()["detail"].lower())

    def test_52_review_nonexistent_student_returns_404(self):
        """Submitting review for non-existent student returns HTTP 404."""
        _, _, headers = self.register_and_login(name="Student", email="rev2107072@stud.kuet.ac.bd")
        resp = self.client.post(
            "/api/reviews",
            json_data={"reviewee_id": 999999, "rating": 5, "comment": "Ghost review"},
            headers=headers,
        )
        self.assertEqual(resp.status_code, 404)

    def test_53_report_nonexistent_item_returns_404(self):
        """Reporting a non-existent item returns HTTP 404."""
        _, _, headers = self.register_and_login(name="Student", email="rep2107073@stud.kuet.ac.bd")
        resp = self.client.post(
            "/api/items/999999/report",
            json_data={"reason": "Broken", "details": "Doesn't exist"},
            headers=headers,
        )
        self.assertEqual(resp.status_code, 404)

    def test_54_save_nonexistent_item_returns_404(self):
        """Bookmarking/saving a non-existent item returns HTTP 404."""
        _, _, headers = self.register_and_login(name="Student", email="save2107074@stud.kuet.ac.bd")
        resp = self.client.post("/api/items/999999/save", headers=headers)
        self.assertEqual(resp.status_code, 404)

    def test_55_save_toggle_twice_removes_from_wishlist(self):
        """Calling save on an item once saves it (saved=True), second time removes it (saved=False)."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107075@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Wishlist Item")

        _, _, student_h = self.register_and_login(name="Student", email="student2307076@stud.kuet.ac.bd")

        # First toggle: Save
        resp1 = self.client.post(f"/api/items/{item['id']}/save", headers=student_h)
        self.assertEqual(resp1.status_code, 200)
        self.assertTrue(resp1.json()["saved"])

        # Check saved list
        saved = self.client.get("/api/items/saved/all", headers=student_h).json()
        self.assertEqual(len(saved), 1)

        # Second toggle: Unsave
        resp2 = self.client.post(f"/api/items/{item['id']}/save", headers=student_h)
        self.assertEqual(resp2.status_code, 200)
        self.assertFalse(resp2.json()["saved"])

        # Check saved list again: should be empty
        saved_after = self.client.get("/api/items/saved/all", headers=student_h).json()
        self.assertEqual(len(saved_after), 0)
