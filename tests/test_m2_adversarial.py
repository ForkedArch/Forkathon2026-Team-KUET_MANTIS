"""
Milestone 2 Empirical Adversarial Test Suite
KUET CampusShare: Rigorous Challenge Harness by Challenger 1

Stress-tests:
1. JWT token sub parsing with malformed, float, negative, and non-numeric values in get_current_user and get_current_user_optional.
2. Borrow request lifecycle: self-borrowing rejection, duplicate request guards, competing requests auto-decline on acceptance, authorization checks.
3. Handover and return mechanics: OTP generation & verification transitions, return on-time vs late Karma updates (+10 lender, +5 on-time borrower, -30 late borrower), cumulative karma tracking.
"""

import sys
import unittest
import datetime
from pathlib import Path
from jose import jwt, exceptions as jose_exceptions
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

# Add project root and backend directory to path
repo_root = Path(__file__).resolve().parent.parent
backend_dir = repo_root / "backend"
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from tests.base import BaseE2ETestCase
from app import models, database, auth
import asyncio


class TestAdversarialJWTSubParsing(BaseE2ETestCase):
    """
    Adversarial stress-testing of JWT token sub parsing in get_current_user.
    Verifies that malformed, float, negative, non-numeric, and extreme values
    always result in HTTP 401 Unauthorized instead of uncaught HTTP 500 crashes.
    """

    def setUp(self):
        super().setUp()
        # Register a valid student user for reference
        self.reg_user, self.token, self.headers = self.register_and_login(
            name="Valid Student",
            email="valid2107001@stud.kuet.ac.bd",
            password="validPassword123!",
        )

    def test_01_non_numeric_string_sub_rejected_with_401(self):
        """String sub with alphabetical/alphanumeric values returns HTTP 401, not HTTP 500."""
        adversarial_subs = [
            "non_numeric_abc",
            "admin",
            "user_999",
            "123a",
            "None",
            "null",
            "undefined",
            "!@#$%^&*()",
            "0x1A",             # Hex string
            "12 34",            # Space in between
            "sub-string-id",
        ]
        for sub in adversarial_subs:
            token = jwt.encode({"sub": sub}, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
            resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(
                resp.status_code, 401,
                f"Sub '{sub}' did not return HTTP 401! Got {resp.status_code}: {resp.text}"
            )
            self.assertIn("invalid credentials", resp.json().get("detail", "").lower())

    def test_02_empty_and_whitespace_sub_rejected_with_401(self):
        """Empty or whitespace-only sub returns HTTP 401, not HTTP 500."""
        whitespace_subs = [
            "",
            " ",
            "    ",
            "\t",
            "\n",
            "\r\n",
            " \t\n ",
        ]
        for sub in whitespace_subs:
            token = jwt.encode({"sub": sub}, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
            resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(
                resp.status_code, 401,
                f"Whitespace sub '{repr(sub)}' got {resp.status_code}"
            )

    def test_03_float_sub_rejected_with_401(self):
        """Float sub formatted as string or numeric returns HTTP 401, not HTTP 500."""
        # String float values (int(user_id) raises ValueError)
        float_str_subs = [
            "12.34",
            "1.0",
            "0.0001",
            "9999.99",
            "-12.34",
            "1e5",
            "inf",
            "-inf",
            "nan",
        ]
        for sub in float_str_subs:
            token = jwt.encode({"sub": sub}, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
            resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(
                resp.status_code, 401,
                f"Float string sub '{sub}' got {resp.status_code}: {resp.text}"
            )

        # Numeric float values in JWT payload (JWTClaimsError: Subject must be a string)
        numeric_floats = [12.34, 1.0, 0.5, -9.9]
        for num in numeric_floats:
            token = jwt.encode({"sub": num}, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
            resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(
                resp.status_code, 401,
                f"Numeric float sub '{num}' got {resp.status_code}: {resp.text}"
            )

    def test_04_negative_sub_rejected_with_401(self):
        """Negative sub (both string and numeric) returns HTTP 401."""
        negative_subs = [
            "-1",
            "-5",
            "-999999",
            "-0",
        ]
        for sub in negative_subs:
            token = jwt.encode({"sub": sub}, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
            resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(
                resp.status_code, 401,
                f"Negative sub '{sub}' got {resp.status_code}: {resp.text}"
            )

        # Numeric negative integer
        token_num_neg = jwt.encode({"sub": -1}, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
        resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_num_neg}"})
        self.assertEqual(resp.status_code, 401)

    def test_05_extreme_and_structured_sub_values(self):
        """Array, dict, boolean, and null-byte sub values are safely rejected with HTTP 401."""
        complex_subs = [
            [1, 2, 3],
            {"id": 1},
            True,
            False,
            None,
        ]
        for val in complex_subs:
            payload = {"sub": val} if val is not None else {}
            token = jwt.encode(payload, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
            resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(
                resp.status_code, 401,
                f"Complex sub '{val}' got {resp.status_code}"
            )

        # Null byte in sub string
        token_null = jwt.encode({"sub": "1\x00"}, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
        resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_null}"})
        self.assertEqual(resp.status_code, 401)

        # Large numeric string within 64-bit integer range
        token_large = jwt.encode({"sub": "999999999"}, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
        resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_large}"})
        self.assertEqual(resp.status_code, 401)

    def test_06_direct_unit_test_get_current_user_edge_cases(self):
        """Directly invoke auth.get_current_user with edge case tokens."""
        cases = [
            "non_numeric",
            "12.34",
            "-9999",
            "",
            "   ",
        ]
        for val in cases:
            token = jwt.encode({"sub": val}, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(auth.get_current_user(creds, self.db))
            self.assertEqual(ctx.exception.status_code, 401)

    def test_07_get_current_user_optional_returns_none_on_malformed_sub(self):
        """auth.get_current_user_optional returns None without raising 500 on malformed sub."""
        cases = [
            "non_numeric",
            "12.34",
            "-9999",
            "",
        ]
        for val in cases:
            token = jwt.encode({"sub": val}, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
            result = asyncio.run(auth.get_current_user_optional(creds, self.db))
            self.assertIsNone(result)

    def test_08_integer_overflow_sub_unhandled_in_auth(self):
        """
        Adversarial Finding: A sub claim exceeding 64-bit integer size raises OverflowError
        from the database driver because auth.py only catches (JWTError, ValueError).
        Empirically verifies this boundary condition.
        """
        token_huge = jwt.encode({"sub": "9" * 40}, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
        creds_huge = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_huge)
        with self.assertRaises((OverflowError, Exception)) as ctx:
            asyncio.run(auth.get_current_user(creds_huge, self.db))
        # Confirms the unhandled exception is an OverflowError
        self.assertIsInstance(ctx.exception, OverflowError)


class TestAdversarialBorrowLifecycle(BaseE2ETestCase):
    """
    Adversarial stress-testing of borrow requests lifecycle:
    - Self-borrowing rejection & integrity
    - Duplicate request guards under sequential and altered submissions
    - Schema validation on duration_hours (gt=0)
    - Status transitions and ownership authorization
    - Competing requests auto-decline on acceptance
    """

    def setUp(self):
        super().setUp()
        # Create Owner
        self.owner, self.owner_token, self.owner_headers = self.register_and_login(
            name="Item Owner",
            email="owner2107001@stud.kuet.ac.bd",
            password="OwnerPassword123!",
        )
        # Create primary Item
        self.item = self.create_item(
            auth_headers=self.owner_headers,
            title="Adversarial Multimeter",
            category="Electronics",
            condition="Like New",
        )

    def test_01_self_borrowing_strict_rejection(self):
        """Owner attempting to borrow their own item is strictly rejected with HTTP 400."""
        resp = self.create_borrow_request(
            auth_headers=self.owner_headers,
            item_id=self.item["id"],
            duration_hours=24,
            purpose="Self-borrow test",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("cannot request your own item", resp.json().get("detail", "").lower())

        # Verify DB state: no request created, item still available
        req_count = self.db.query(models.BorrowRequest).filter(
            models.BorrowRequest.item_id == self.item["id"]
        ).count()
        self.assertEqual(req_count, 0)

        db_item = self.db.query(models.Item).filter(models.Item.id == self.item["id"]).first()
        self.assertTrue(db_item.is_available)

    def test_02_duplicate_pending_request_guard(self):
        """Borrower cannot spam multiple pending requests for the same item."""
        _, _, borrower_headers = self.register_and_login(
            name="Borrower One",
            email="borrower2107002@stud.kuet.ac.bd",
            password="Password123!",
        )
        # First request succeeds
        resp1 = self.create_borrow_request(
            auth_headers=borrower_headers,
            item_id=self.item["id"],
            duration_hours=24,
            purpose="First attempt",
        )
        self.assertEqual(resp1.status_code, 200)

        # Second request with identical payload rejected
        resp2 = self.create_borrow_request(
            auth_headers=borrower_headers,
            item_id=self.item["id"],
            duration_hours=24,
            purpose="First attempt",
        )
        self.assertEqual(resp2.status_code, 400)
        self.assertIn("already have a pending request", resp2.json().get("detail", "").lower())

        # Third request with altered message & duration also rejected
        resp3 = self.create_borrow_request(
            auth_headers=borrower_headers,
            item_id=self.item["id"],
            duration_hours=48,
            purpose="Second attempt with different purpose",
            message="Please accept!",
        )
        self.assertEqual(resp3.status_code, 400)
        self.assertIn("already have a pending request", resp3.json().get("detail", "").lower())

        # Verify exactly one pending request exists in DB
        pending_count = self.db.query(models.BorrowRequest).filter(
            models.BorrowRequest.item_id == self.item["id"],
            models.BorrowRequest.status == "pending",
        ).count()
        self.assertEqual(pending_count, 1)

    def test_03_re_request_permitted_after_decline(self):
        """Borrower can submit a new request if their prior request was declined."""
        _, _, borrower_headers = self.register_and_login(
            name="Borrower Declined",
            email="declined2107003@stud.kuet.ac.bd",
            password="Password123!",
        )
        req = self.create_borrow_request(
            auth_headers=borrower_headers,
            item_id=self.item["id"],
        ).json()

        # Owner declines the request
        dec_resp = self.client.put(
            f"/api/requests/{req['id']}/status",
            json_data={"status": "declined"},
            headers=self.owner_headers,
        )
        self.assertEqual(dec_resp.status_code, 200)

        # Now borrower submits a fresh request — must succeed
        new_resp = self.create_borrow_request(
            auth_headers=borrower_headers,
            item_id=self.item["id"],
            purpose="Trying again with better explanation",
        )
        self.assertEqual(new_resp.status_code, 200)
        self.assertEqual(new_resp.json()["status"], "pending")

    def test_04_request_unavailable_item_rejected(self):
        """Attempting to request an unavailable item is rejected with HTTP 400."""
        # Manually mark item unavailable
        db_item = self.db.query(models.Item).filter(models.Item.id == self.item["id"]).first()
        db_item.is_available = False
        self.db.commit()

        _, _, borrower_headers = self.register_and_login(
            name="Borrower Unavail",
            email="unavail2107004@stud.kuet.ac.bd",
            password="Password123!",
        )
        resp = self.create_borrow_request(
            auth_headers=borrower_headers,
            item_id=self.item["id"],
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("not available", resp.json().get("detail", "").lower())

    def test_05_status_update_authorization_and_immutability(self):
        """Only the owner can update status, and resolved requests cannot be altered."""
        _, _, borrower_headers = self.register_and_login(
            name="Borrower Auth",
            email="borrowauth2107005@stud.kuet.ac.bd",
            password="Password123!",
        )
        _, _, stranger_headers = self.register_and_login(
            name="Stranger",
            email="stranger2107006@stud.kuet.ac.bd",
            password="Password123!",
        )
        req = self.create_borrow_request(
            auth_headers=borrower_headers,
            item_id=self.item["id"],
        ).json()

        # Borrower attempts to accept
        resp1 = self.client.put(
            f"/api/requests/{req['id']}/status",
            json_data={"status": "accepted"},
            headers=borrower_headers,
        )
        self.assertEqual(resp1.status_code, 403)

        # Stranger attempts to decline
        resp2 = self.client.put(
            f"/api/requests/{req['id']}/status",
            json_data={"status": "declined"},
            headers=stranger_headers,
        )
        self.assertEqual(resp2.status_code, 403)

        # Owner accepts
        resp3 = self.client.put(
            f"/api/requests/{req['id']}/status",
            json_data={"status": "accepted"},
            headers=self.owner_headers,
        )
        self.assertEqual(resp3.status_code, 200)

        # Owner attempts to re-accept or decline an already accepted request
        resp4 = self.client.put(
            f"/api/requests/{req['id']}/status",
            json_data={"status": "accepted"},
            headers=self.owner_headers,
        )
        self.assertEqual(resp4.status_code, 400)
        self.assertIn("already been resolved", resp4.json().get("detail", "").lower())

        resp5 = self.client.put(
            f"/api/requests/{req['id']}/status",
            json_data={"status": "declined"},
            headers=self.owner_headers,
        )
        self.assertEqual(resp5.status_code, 400)
        self.assertIn("already been resolved", resp5.json().get("detail", "").lower())

    def test_06_competing_requests_auto_decline_on_acceptance(self):
        """When owner accepts one request, all competing pending requests are auto-declined."""
        borrowers = []
        for i in range(1, 6):
            _, _, h = self.register_and_login(
                name=f"Competing Borrower {i}",
                email=f"compete{i}21070{10+i}@stud.kuet.ac.bd",
                password="Password123!",
            )
            req = self.create_borrow_request(
                auth_headers=h,
                item_id=self.item["id"],
                purpose=f"Competing request {i}",
            ).json()
            borrowers.append((i, h, req))

        # Verify all 5 are pending
        for i, h, req in borrowers:
            db_req = self.db.query(models.BorrowRequest).filter(models.BorrowRequest.id == req["id"]).first()
            self.assertEqual(db_req.status, "pending")

        # Owner accepts Borrower 3 (index 2)
        accepted_req = borrowers[2][2]
        resp_acc = self.client.put(
            f"/api/requests/{accepted_req['id']}/status",
            json_data={"status": "accepted"},
            headers=self.owner_headers,
        )
        self.assertEqual(resp_acc.status_code, 200)

        # Re-fetch all requests from DB to verify statuses
        for i, h, req in borrowers:
            db_req = self.db.query(models.BorrowRequest).filter(models.BorrowRequest.id == req["id"]).first()
            if req["id"] == accepted_req["id"]:
                self.assertEqual(db_req.status, "accepted", f"Request {req['id']} should be accepted")
            else:
                self.assertEqual(
                    db_req.status, "declined",
                    f"Competing request {req['id']} (borrower {i}) was not auto-declined!"
                )

        # Verify item availability is False
        db_item = self.db.query(models.Item).filter(models.Item.id == self.item["id"]).first()
        self.assertFalse(db_item.is_available)

        # Verify Owner cannot accept any of the auto-declined requests
        for i, h, req in borrowers:
            if req["id"] != accepted_req["id"]:
                fail_resp = self.client.put(
                    f"/api/requests/{req['id']}/status",
                    json_data={"status": "accepted"},
                    headers=self.owner_headers,
                )
                self.assertEqual(fail_resp.status_code, 400)

        # Verify a new borrower cannot create a request on the now unavailable item
        _, _, b6_h = self.register_and_login(
            name="Late Borrower 6",
            email="late62107019@stud.kuet.ac.bd",
            password="Password123!",
        )
        b6_resp = self.create_borrow_request(auth_headers=b6_h, item_id=self.item["id"])
        self.assertEqual(b6_resp.status_code, 400)
        self.assertIn("not available", b6_resp.json().get("detail", "").lower())

    def test_07_duration_hours_schema_validation(self):
        """Zero and negative duration_hours values are rejected by schema validation (HTTP 422)."""
        _, _, b_h = self.register_and_login(
            name="Duration Tester",
            email="duration2107020@stud.kuet.ac.bd",
            password="Password123!",
        )
        # 0 duration
        resp_zero = self.client.post("/api/requests", json_data={
            "item_id": self.item["id"],
            "duration_hours": 0,
        }, headers=b_h)
        self.assertEqual(resp_zero.status_code, 422)

        # Negative duration
        resp_neg = self.client.post("/api/requests", json_data={
            "item_id": self.item["id"],
            "duration_hours": -5,
        }, headers=b_h)
        self.assertEqual(resp_neg.status_code, 422)


class TestAdversarialHandoverAndReturnMechanics(BaseE2ETestCase):
    """
    Adversarial stress-testing of OTP handover and item return mechanics:
    - 4-digit OTP format, QR code validity, and sensitive data wiping
    - Ownership & role security (owner-only start, borrower-only verify/return)
    - Karma engine protocol (+10 lender, +5 on-time borrower, -30 late borrower)
    - Cumulative tracking across multiple sequential transactions
    """

    def setUp(self):
        super().setUp()
        # Register Owner
        self.owner, self.owner_token, self.owner_headers = self.register_and_login(
            name="Handover Owner",
            email="howner2107021@stud.kuet.ac.bd",
            password="OwnerPassword123!",
        )
        # Register Borrower
        self.borrower, self.borrower_token, self.borrower_headers = self.register_and_login(
            name="Handover Borrower",
            email="hborrower2107022@stud.kuet.ac.bd",
            password="BorrowerPassword123!",
        )
        # Create Item
        self.item = self.create_item(
            auth_headers=self.owner_headers,
            title="Lab Oscilloscope",
            category="Electronics",
        )

    def test_01_handover_start_authorization_and_preconditions(self):
        """Only owner can start handover, and request must already be accepted."""
        # Create pending request
        req = self.create_borrow_request(
            auth_headers=self.borrower_headers,
            item_id=self.item["id"],
        ).json()

        # Borrower tries to start handover -> 403
        resp1 = self.client.post(
            "/api/transactions/start",
            json_data={"request_id": req["id"]},
            headers=self.borrower_headers,
        )
        self.assertEqual(resp1.status_code, 403)

        # Owner tries to start before accepting -> 400
        resp2 = self.client.post(
            "/api/transactions/start",
            json_data={"request_id": req["id"]},
            headers=self.owner_headers,
        )
        self.assertEqual(resp2.status_code, 400)
        self.assertIn("not accepted", resp2.json().get("detail", "").lower())

        # Non-existent request ID -> 404
        resp3 = self.client.post(
            "/api/transactions/start",
            json_data={"request_id": 999999},
            headers=self.owner_headers,
        )
        self.assertEqual(resp3.status_code, 404)

    def test_02_otp_format_qr_generation_and_clearing(self):
        """OTP is exactly 4 digits, QR code is valid data URI, and both are wiped after verification."""
        req = self.create_borrow_request(auth_headers=self.borrower_headers, item_id=self.item["id"]).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=self.owner_headers)

        # Start transaction
        start_resp = self.client.post(
            "/api/transactions/start",
            json_data={"request_id": req["id"]},
            headers=self.owner_headers,
        )
        self.assertEqual(start_resp.status_code, 200)
        data = start_resp.json()
        otp = data["otp"]
        qr_code = data["qr_code"]

        # Validate OTP format (4 digits)
        self.assertEqual(len(otp), 4)
        self.assertTrue(otp.isdigit(), f"OTP '{otp}' must be all digits")

        # Validate QR code base64 format
        self.assertTrue(qr_code.startswith("data:image/png;base64,"))

        # Check DB before verification
        trans_before = self.db.query(models.Transaction).filter(models.Transaction.request_id == req["id"]).first()
        self.assertEqual(trans_before.status, "pending")
        self.assertEqual(trans_before.otp, otp)
        self.assertIsNotNone(trans_before.qr_code)

        # Verify handover as borrower
        verify_resp = self.client.post(
            "/api/transactions/verify",
            json_data={"request_id": req["id"], "otp": otp},
            headers=self.borrower_headers,
        )
        self.assertEqual(verify_resp.status_code, 200)

        # Check DB after verification: OTP and QR code must be cleared
        self.db.expire_all()
        trans_after = self.db.query(models.Transaction).filter(models.Transaction.request_id == req["id"]).first()
        self.assertEqual(trans_after.status, "borrowed")
        self.assertIsNone(trans_after.otp, "trans.otp must be wiped after verification for security!")
        self.assertIsNone(trans_after.qr_code, "trans.qr_code must be wiped after verification!")
        self.assertIsNotNone(trans_after.borrowed_at)

    def test_03_otp_verification_adversarial_inputs(self):
        """OTP verification rejects wrong digits, wrong length, non-numeric, and unauthorized callers."""
        req = self.create_borrow_request(auth_headers=self.borrower_headers, item_id=self.item["id"]).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=self.owner_headers)
        start = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=self.owner_headers).json()
        real_otp = start["otp"]

        # Owner tries to verify -> 403
        resp_own = self.client.post(
            "/api/transactions/verify",
            json_data={"request_id": req["id"], "otp": real_otp},
            headers=self.owner_headers,
        )
        self.assertEqual(resp_own.status_code, 403)

        # Incorrect OTP inputs from borrower
        bad_otps = [
            "0000" if real_otp != "0000" else "1111",
            "123",        # 3 digits
            "12345",      # 5 digits
            "abcd",       # Alpha
            "!@#$",       # Symbols
            " ",          # Whitespace
        ]
        for bad_otp in bad_otps:
            resp_bad = self.client.post(
                "/api/transactions/verify",
                json_data={"request_id": req["id"], "otp": bad_otp},
                headers=self.borrower_headers,
            )
            self.assertEqual(resp_bad.status_code, 400)
            self.assertIn("invalid otp", resp_bad.json().get("detail", "").lower())

        # Correct OTP succeeds
        resp_ok = self.client.post(
            "/api/transactions/verify",
            json_data={"request_id": req["id"], "otp": real_otp},
            headers=self.borrower_headers,
        )
        self.assertEqual(resp_ok.status_code, 200)

        # Re-verification attempt fails
        resp_again = self.client.post(
            "/api/transactions/verify",
            json_data={"request_id": req["id"], "otp": real_otp},
            headers=self.borrower_headers,
        )
        self.assertEqual(resp_again.status_code, 400)

    def test_04_on_time_return_karma_award(self):
        """On-time return awards +10 Karma to Owner and +5 Karma to Borrower."""
        req = self.create_borrow_request(
            auth_headers=self.borrower_headers,
            item_id=self.item["id"],
            duration_hours=24,
        ).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=self.owner_headers)
        start = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=self.owner_headers).json()
        self.client.post("/api/transactions/verify", json_data={"request_id": req["id"], "otp": start["otp"]}, headers=self.borrower_headers)

        # Simulate borrowed 2 hours ago (well within 24h duration)
        trans = self.db.query(models.Transaction).filter(models.Transaction.request_id == req["id"]).first()
        trans.borrowed_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)
        self.db.commit()

        # Borrower returns item
        ret_resp = self.client.post(f"/api/transactions/return/{req['id']}", headers=self.borrower_headers)
        self.assertEqual(ret_resp.status_code, 200)
        data = ret_resp.json()

        karma_info = data["karma_updated"]
        self.assertTrue(karma_info["is_on_time"])
        self.assertEqual(karma_info["owner_gain"], 10)
        self.assertEqual(karma_info["borrower_change"], 5)

        # Verify Owner profile: 100 + 10 = 110
        owner_me = self.client.get("/api/auth/me", headers=self.owner_headers).json()
        self.assertEqual(owner_me["karma"], 110)
        self.assertEqual(owner_me["trust_score"], 110.0)
        self.assertEqual(owner_me["total_lends"], 1)

        # Verify Borrower profile: 100 + 5 = 105
        borrower_me = self.client.get("/api/auth/me", headers=self.borrower_headers).json()
        self.assertEqual(borrower_me["karma"], 105)
        self.assertEqual(borrower_me["trust_score"], 105.0)
        self.assertEqual(borrower_me["total_borrows"], 1)

        # Verify item is restored to available
        db_item = self.db.query(models.Item).filter(models.Item.id == self.item["id"]).first()
        self.assertTrue(db_item.is_available)
        self.assertEqual(db_item.status, "available")

        # Verify request is completed
        db_req = self.db.query(models.BorrowRequest).filter(models.BorrowRequest.id == req["id"]).first()
        self.assertEqual(db_req.status, "completed")

    def test_05_late_return_karma_penalty(self):
        """Late return awards +10 Karma to Owner and penalizes Borrower with -30 Karma."""
        req = self.create_borrow_request(
            auth_headers=self.borrower_headers,
            item_id=self.item["id"],
            duration_hours=4,
        ).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=self.owner_headers)
        start = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=self.owner_headers).json()
        self.client.post("/api/transactions/verify", json_data={"request_id": req["id"], "otp": start["otp"]}, headers=self.borrower_headers)

        # Simulate borrowed 12 hours ago (duration was only 4h -> 8 hours late!)
        trans = self.db.query(models.Transaction).filter(models.Transaction.request_id == req["id"]).first()
        trans.borrowed_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=12)
        self.db.commit()

        # Borrower returns item
        ret_resp = self.client.post(f"/api/transactions/return/{req['id']}", headers=self.borrower_headers)
        self.assertEqual(ret_resp.status_code, 200)
        data = ret_resp.json()

        karma_info = data["karma_updated"]
        self.assertFalse(karma_info["is_on_time"])
        self.assertEqual(karma_info["owner_gain"], 10)
        self.assertEqual(karma_info["borrower_change"], -30)

        # Verify Owner profile: 100 + 10 = 110
        owner_me = self.client.get("/api/auth/me", headers=self.owner_headers).json()
        self.assertEqual(owner_me["karma"], 110)
        self.assertEqual(owner_me["trust_score"], 110.0)
        self.assertEqual(owner_me["total_lends"], 1)

        # Verify Borrower profile: 100 - 30 = 70
        borrower_me = self.client.get("/api/auth/me", headers=self.borrower_headers).json()
        self.assertEqual(borrower_me["karma"], 70)
        self.assertEqual(borrower_me["trust_score"], 70.0)
        self.assertEqual(borrower_me["total_borrows"], 1)

    def test_06_re_return_guard_and_consecutive_lending_karma_accumulation(self):
        """Calling return twice is rejected, and subsequent lendings accumulate Karma correctly."""
        # Transaction 1: On-time return
        req1 = self.create_borrow_request(auth_headers=self.borrower_headers, item_id=self.item["id"], duration_hours=10).json()
        self.client.put(f"/api/requests/{req1['id']}/status", json_data={"status": "accepted"}, headers=self.owner_headers)
        s1 = self.client.post("/api/transactions/start", json_data={"request_id": req1["id"]}, headers=self.owner_headers).json()
        self.client.post("/api/transactions/verify", json_data={"request_id": req1["id"], "otp": s1["otp"]}, headers=self.borrower_headers)
        self.client.post(f"/api/transactions/return/{req1['id']}", headers=self.borrower_headers)

        # Duplicate return attempt rejected
        dup_ret = self.client.post(f"/api/transactions/return/{req1['id']}", headers=self.borrower_headers)
        self.assertEqual(dup_ret.status_code, 400)
        self.assertIn("not currently borrowed", dup_ret.json().get("detail", "").lower())

        # Transaction 2: A second borrower borrows the newly available item
        _, _, b2_headers = self.register_and_login(
            name="Second Borrower",
            email="secondb2107025@stud.kuet.ac.bd",
            password="Password123!",
        )
        req2 = self.create_borrow_request(auth_headers=b2_headers, item_id=self.item["id"], duration_hours=5).json()
        self.client.put(f"/api/requests/{req2['id']}/status", json_data={"status": "accepted"}, headers=self.owner_headers)
        s2 = self.client.post("/api/transactions/start", json_data={"request_id": req2["id"]}, headers=self.owner_headers).json()
        self.client.post("/api/transactions/verify", json_data={"request_id": req2["id"], "otp": s2["otp"]}, headers=b2_headers)
        self.client.post(f"/api/transactions/return/{req2['id']}", headers=b2_headers)

        # Owner accumulated 2 lends: 100 + 10 + 10 = 120 karma
        owner_me = self.client.get("/api/auth/me", headers=self.owner_headers).json()
        self.assertEqual(owner_me["karma"], 120)
        self.assertEqual(owner_me["trust_score"], 120.0)
        self.assertEqual(owner_me["total_lends"], 2)


if __name__ == "__main__":
    unittest.main()
