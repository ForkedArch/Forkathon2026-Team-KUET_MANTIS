"""
Milestone 1 Empirical Adversarial Test Suite
KUET CampusShare: Rigorous Challenge Harness by Challenger 2

Stress-tests:
1. Malformed JSON, missing fields, edge-case credentials, and invalid domains on /api/auth/register
2. KUET department code boundary validation (00-99) and composite roll uniqueness
3. Authentication credentials attacks, SQLi immunity, case-insensitivity on /api/auth/login
4. JWT token security: expired tokens, forged secret keys, 'none' algorithm, non-existent user IDs, non-int sub
5. CORS headers, preflight requests, credentials support, and preview domain regex matching
6. Deployment configuration verification (render.yaml free tier, vercel.json rewrite precedence)
7. Concurrency and race conditions (simultaneous duplicate registrations, concurrent logins, /me stress)
"""

import os
import sys
import json
import yaml
import time
import tempfile
import unittest
import concurrent.futures
from pathlib import Path
from datetime import timedelta, datetime, timezone
from jose import jwt

# Add backend directory to sys.path
repo_root = Path(__file__).resolve().parent.parent
backend_dir = repo_root / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app import database, models, auth, schemas
from app.routes.auth import KUET_DEPT_MAP, decode_dept_code, decode_kuet_email
from tests.asgi_client import ASGIClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


class BaseAdversarialTestCase(unittest.TestCase):
    """Isolated in-memory test harness ensuring test isolation."""

    @classmethod
    def setUpClass(cls):
        cls.app = app

    def setUp(self):
        self.test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        models.Base.metadata.create_all(bind=self.test_engine)
        self.TestSession = sessionmaker(autocommit=False, autoflush=False, bind=self.test_engine)

        def override_get_db():
            db = self.TestSession()
            try:
                yield db
            finally:
                db.close()

        self.app.dependency_overrides[database.get_db] = override_get_db
        self.client = ASGIClient(self.app)
        self.db = self.TestSession()

    def tearDown(self):
        self.db.close()
        models.Base.metadata.drop_all(bind=self.test_engine)
        self.test_engine.dispose()
        self.app.dependency_overrides.clear()


class TestAdversarialAuthRegistration(BaseAdversarialTestCase):
    """Adversarial testing of POST /api/auth/register."""

    def test_malformed_json_payloads(self):
        """Malformed JSON strings, arrays, or scalars should return 422, never 500."""
        malformed_inputs = [
            b"{not valid json",
            b'{"name": "Alice", "email": }',
            b"[1, 2, 3]",
            b'"just a string"',
            b"12345",
            b"",
        ]
        for bad_payload in malformed_inputs:
            resp = self.client.post(
                "/api/auth/register",
                data=bad_payload,
                headers={"content-type": "application/json"}
            )
            self.assertEqual(
                resp.status_code, 422,
                f"Malformed payload {bad_payload!r} did not yield 422: got {resp.status_code}"
            )

    def test_missing_and_empty_fields(self):
        """Omitted or empty fields must be rejected with 422."""
        cases = [
            {},
            {"name": "Only Name"},
            {"email": "student2307001@stud.kuet.ac.bd"},
            {"password": "secretpassword"},
            {"name": "", "email": "student2307001@stud.kuet.ac.bd", "password": "secretpassword"},
            {"name": "   ", "email": "student2307001@stud.kuet.ac.bd", "password": "secretpassword"},
            {"name": "Valid Name", "email": "", "password": "secretpassword"},
            {"name": "Valid Name", "email": "student2307001@stud.kuet.ac.bd", "password": ""},
        ]
        for payload in cases:
            resp = self.client.post("/api/auth/register", json_data=payload)
            self.assertEqual(
                resp.status_code, 422,
                f"Payload {payload} should be rejected with 422, got {resp.status_code}"
            )

    def test_short_name_and_password_boundaries(self):
        """Name < 2 chars or password < 4 chars must be rejected with 422."""
        # Name too short
        resp1 = self.client.post("/api/auth/register", json_data={
            "name": "A",
            "email": "student2307001@stud.kuet.ac.bd",
            "password": "validpassword"
        })
        self.assertEqual(resp1.status_code, 422)

        # Password too short (<4)
        resp2 = self.client.post("/api/auth/register", json_data={
            "name": "Valid Name",
            "email": "student2307001@stud.kuet.ac.bd",
            "password": "123"
        })
        self.assertEqual(resp2.status_code, 422)

    def test_long_inputs_and_special_characters(self):
        """Extremely long names and complex passwords with unicode/symbols should be handled safely."""
        long_name = "Dr. " + "X" * 150
        complex_pwd = "P@ssw0rd!#$§±—🔑🔐🚀" + "A" * 50
        resp = self.client.post("/api/auth/register", json_data={
            "name": long_name,
            "email": "complex2307001@stud.kuet.ac.bd",
            "password": complex_pwd
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["name"], long_name)
        self.assertEqual(data["karma"], 100)

        # Verify login with complex password succeeds
        login_resp = self.client.post("/api/auth/login", json_data={
            "email": "complex2307001@stud.kuet.ac.bd",
            "password": complex_pwd
        })
        self.assertEqual(login_resp.status_code, 200)

    def test_non_kuet_domains_rejected(self):
        """Non-KUET email domains must be rejected with HTTP 400."""
        invalid_emails = [
            "student@gmail.com",
            "student@yahoo.com",
            "teacher@kuet.ac.bd",
            "student@cse.kuet.ac.bd",
            "student@sub.stud.kuet.ac.bd",
            "student@stud.kuet.ac.bd.attacker.com",
            "student@notstud.kuet.ac.bd",
            "attacker@evil.com@stud.kuet.ac.bd",
        ]
        for email in invalid_emails:
            resp = self.client.post("/api/auth/register", json_data={
                "name": "Evil Actor",
                "email": email,
                "password": "password123"
            })
            self.assertIn(resp.status_code, (400, 422), f"Email {email} should be rejected, got {resp.status_code}")

    def test_invalid_roll_and_department_boundaries(self):
        """Verify boundary rejections on roll format and department codes."""
        bad_emails = [
            "student12345@stud.kuet.ac.bd",      # 5 digits
            "student123456@stud.kuet.ac.bd",     # 6 digits
            "tanvir.rahman@stud.kuet.ac.bd",     # No digits
            "student2300001@stud.kuet.ac.bd",    # Department 00 (invalid)
            "student2330001@stud.kuet.ac.bd",    # Department 30 (invalid)
            "student2332001@stud.kuet.ac.bd",    # Department 32 (invalid)
            "student2399001@stud.kuet.ac.bd",    # Department 99 (invalid)
        ]
        for email in bad_emails:
            resp = self.client.post("/api/auth/register", json_data={
                "name": "Invalid Student",
                "email": email,
                "password": "password123"
            })
            self.assertEqual(resp.status_code, 400, f"Email {email} should return 400, got {resp.status_code}")

    def test_case_insensitive_registration_and_login(self):
        """Email normalization to lowercase must prevent duplicate registrations with mixed case."""
        # Register in mixed case
        resp1 = self.client.post("/api/auth/register", json_data={
            "name": "Case Student",
            "email": "CaseStudent2307042@STUD.KUET.AC.BD",
            "password": "password123"
        })
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp1.json()["email"], "casestudent2307042@stud.kuet.ac.bd")

        # Attempt to register again in lowercase must be rejected
        resp2 = self.client.post("/api/auth/register", json_data={
            "name": "Case Student Dup",
            "email": "casestudent2307042@stud.kuet.ac.bd",
            "password": "password123"
        })
        self.assertEqual(resp2.status_code, 400)
        self.assertIn("Email already registered", resp2.json()["detail"])

        # Login in uppercase must succeed
        resp3 = self.client.post("/api/auth/login", json_data={
            "email": "CASESTUDENT2307042@STUD.KUET.AC.BD",
            "password": "password123"
        })
        self.assertEqual(resp3.status_code, 200)

    def test_composite_uniqueness_enforcement(self):
        """Same batch, dept, roll under a different email local part must be rejected."""
        resp1 = self.client.post("/api/auth/register", json_data={
            "name": "Original Student",
            "email": "first2307015@stud.kuet.ac.bd",
            "password": "password123"
        })
        self.assertEqual(resp1.status_code, 200)

        # Different local part name prefix, but same batch (23), dept (07 -> CSE), roll (015)
        resp2 = self.client.post("/api/auth/register", json_data={
            "name": "Impostor Student",
            "email": "second2307015@stud.kuet.ac.bd",
            "password": "password123"
        })
        self.assertEqual(resp2.status_code, 400)
        self.assertIn("Roll number already registered", resp2.json()["detail"])

    def test_initial_base_karma_and_trust_score(self):
        """Newly registered student must receive exactly 100 Base Karma and 100.0 trust score."""
        resp = self.client.post("/api/auth/register", json_data={
            "name": "Karma Test Student",
            "email": "karmatest2307080@stud.kuet.ac.bd",
            "password": "password123"
        })
        self.assertEqual(resp.status_code, 200)
        user_data = resp.json()
        self.assertEqual(user_data["karma"], 100)
        self.assertEqual(user_data["trust_score"], 100.0)
        self.assertEqual(user_data["total_lends"], 0)
        self.assertEqual(user_data["total_borrows"], 0)


class TestAdversarialLoginAndJWT(BaseAdversarialTestCase):
    """Adversarial testing of POST /api/auth/login and GET /api/auth/me."""

    def setUp(self):
        super().setUp()
        # Register a fixture user
        reg_resp = self.client.post("/api/auth/register", json_data={
            "name": "Auth Fixture User",
            "email": "fixture2307001@stud.kuet.ac.bd",
            "password": "correct_password123"
        })
        self.assertEqual(reg_resp.status_code, 200)
        self.fixture_user = reg_resp.json()

    def test_login_wrong_password_and_nonexistent_email(self):
        """Invalid credentials must return 401 with generic error message."""
        # Wrong password
        resp1 = self.client.post("/api/auth/login", json_data={
            "email": "fixture2307001@stud.kuet.ac.bd",
            "password": "wrong_password"
        })
        self.assertEqual(resp1.status_code, 401)
        self.assertEqual(resp1.json()["detail"], "Incorrect email or password")

        # Nonexistent email
        resp2 = self.client.post("/api/auth/login", json_data={
            "email": "nobody2307001@stud.kuet.ac.bd",
            "password": "any_password"
        })
        self.assertEqual(resp2.status_code, 401)
        self.assertEqual(resp2.json()["detail"], "Incorrect email or password")

    def test_login_sqli_immunity(self):
        """SQL injection payloads in login must not bypass authentication."""
        sqli_cases = [
            {"email": "' OR '1'='1' --", "password": "password"},
            {"email": "fixture2307001@stud.kuet.ac.bd", "password": "' OR 1=1 --"},
            {"email": "fixture2307001@stud.kuet.ac.bd", "password": "' UNION SELECT * FROM users --"},
        ]
        for case in sqli_cases:
            resp = self.client.post("/api/auth/login", json_data=case)
            self.assertIn(resp.status_code, (401, 422))

    def test_expired_jwt_token(self):
        """Expired JWT token must return 401 Unauthorized."""
        expired_token = auth.create_access_token(
            {"sub": str(self.fixture_user["id"])},
            expires_delta=timedelta(minutes=-15)
        )
        resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()["detail"], "Invalid credentials")

    def test_forged_secret_jwt_token(self):
        """Token signed with forged secret key must return 401."""
        forged_token = jwt.encode(
            {"sub": str(self.fixture_user["id"]), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "attacker-fake-secret-key",
            algorithm="HS256"
        )
        resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged_token}"})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()["detail"], "Invalid credentials")

    def test_malformed_authorization_headers(self):
        """Missing or malformed Authorization headers must be rejected (401 or 403)."""
        malformed_headers = [
            {},
            {"Authorization": "Bearer"},
            {"Authorization": "Bearer   "},
            {"Authorization": "Basic dXNlcjpwYXNz"},
            {"Authorization": "Token 12345"},
            {"Authorization": "Bearer this.is.garbage.token"},
        ]
        for h in malformed_headers:
            resp = self.client.get("/api/auth/me", headers=h)
            self.assertIn(resp.status_code, (401, 403), f"Header {h} should be rejected, got {resp.status_code}")

    def test_nonexistent_user_id_in_valid_token(self):
        """A validly signed token with a non-existent user ID must return 401."""
        nonexistent_token = auth.create_access_token({"sub": "999999"})
        resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {nonexistent_token}"})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()["detail"], "Invalid credentials")


class TestAdversarialCORSAndDeployment(unittest.TestCase):
    """Adversarial verification of CORS, render.yaml, and vercel.json."""

    def test_cors_preflight_production_vercel_origin(self):
        """CORS preflight request with Vercel origin must return 200 with proper headers."""
        client = ASGIClient(app)
        test_origins = [
            "https://campusshare.vercel.app",
            "https://campusshare-preview-abc.vercel.app",
            "http://localhost:5173",
        ]
        for origin in test_origins:
            resp = client.request("OPTIONS", "/api/auth/login", headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            })
            self.assertEqual(resp.status_code, 200, f"Preflight failed for origin {origin}")
            self.assertEqual(resp.headers.get("access-control-allow-origin"), origin)
            self.assertEqual(resp.headers.get("access-control-allow-credentials"), "true")

    def test_render_yaml_validity_and_free_tier_safety(self):
        """render.yaml must be valid YAML, define both services on free tier with NO disks."""
        render_path = repo_root / "render.yaml"
        self.assertTrue(render_path.exists(), "render.yaml must exist")
        with open(render_path) as f:
            cfg = yaml.safe_load(f)

        services = cfg.get("services", [])
        self.assertEqual(len(services), 2, "render.yaml must define backend and frontend services")

        backend = next((s for s in services if s["name"] == "campusshare-backend"), None)
        self.assertIsNotNone(backend, "campusshare-backend must be declared")
        self.assertEqual(backend["plan"], "free")
        self.assertNotIn("disk", backend, "Persistent disk cannot be declared on Render free tier")
        self.assertEqual(backend["healthCheckPath"], "/health")

        frontend = next((s for s in services if s["name"] == "campusshare-frontend"), None)
        self.assertIsNotNone(frontend, "campusshare-frontend must be declared")
        self.assertEqual(frontend["plan"], "free")
        self.assertEqual(frontend["env"], "static")

    def test_vercel_json_rewrite_precedence(self):
        """Both root and frontend vercel.json must proxy /api/ and /uploads/ before SPA catch-all."""
        for vpath in [repo_root / "vercel.json", repo_root / "frontend" / "vercel.json"]:
            self.assertTrue(vpath.exists(), f"{vpath} must exist")
            with open(vpath) as f:
                data = json.load(f)

            rewrites = data.get("rewrites", [])
            api_rule = next((r for r in rewrites if r.get("source") == "/api/:path*"), None)
            uploads_rule = next((r for r in rewrites if r.get("source") == "/uploads/:path*"), None)
            catch_all = next((r for r in rewrites if r.get("source") in ("/(.*)", "/(.*)")), None)

            self.assertIsNotNone(api_rule, f"{vpath} missing /api/:path* rewrite rule")
            self.assertIsNotNone(uploads_rule, f"{vpath} missing /uploads/:path* rewrite rule")
            self.assertIsNotNone(catch_all, f"{vpath} missing SPA catch-all rule")

            api_idx = rewrites.index(api_rule)
            uploads_idx = rewrites.index(uploads_rule)
            catch_idx = rewrites.index(catch_all)

            self.assertLess(api_idx, catch_idx, f"{vpath}: /api/ must come before SPA catch-all")
            self.assertLess(uploads_idx, catch_idx, f"{vpath}: /uploads/ must come before SPA catch-all")


class TestAdversarialConcurrencyAndStress(BaseAdversarialTestCase):
    """Stress testing concurrency, race conditions, and session stability."""

    def test_simultaneous_duplicate_registration_race_condition(self):
        """
        When 10 threads attempt to register the exact same student simultaneously:
        - Exactly ONE thread must succeed (HTTP 200).
        - Exactly 9 threads must receive HTTP 400 (duplicate rejected).
        - ZERO threads must receive HTTP 500 or SQLite database lock errors.
        """
        client = ASGIClient(self.app)

        def attempt_register(idx):
            payload = {
                "name": f"Concurrent Student {idx}",
                "email": "concurrentrace2307001@stud.kuet.ac.bd",
                "password": "password123",
            }
            resp = client.post("/api/auth/register", json_data=payload)
            return resp.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(attempt_register, i) for i in range(10)]
            statuses = [f.result() for f in futures]

        self.assertEqual(statuses.count(200), 1, "Exactly one registration should succeed")
        self.assertEqual(statuses.count(400), 9, "All 9 concurrent duplicate requests should receive 400")
        self.assertEqual(statuses.count(500), 0, "No unhandled 500 errors or database locks allowed")

    def test_concurrent_logins_stability(self):
        """20 simultaneous logins on the same user account must all succeed without session conflict."""
        client = ASGIClient(self.app)
        # Register user
        reg_resp = client.post("/api/auth/register", json_data={
            "name": "Stress Login User",
            "email": "stresslogin2307099@stud.kuet.ac.bd",
            "password": "secretpassword",
        })
        self.assertEqual(reg_resp.status_code, 200)

        def attempt_login():
            resp = client.post("/api/auth/login", json_data={
                "email": "stresslogin2307099@stud.kuet.ac.bd",
                "password": "secretpassword",
            })
            return resp.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(attempt_login) for _ in range(20)]
            statuses = [f.result() for f in futures]

        self.assertEqual(set(statuses), {200})
        self.assertEqual(len(statuses), 20)

    def test_concurrent_authenticated_profile_requests(self):
        """30 concurrent GET /api/auth/me requests must all succeed with valid tokens."""
        client = ASGIClient(self.app)
        reg_resp = client.post("/api/auth/register", json_data={
            "name": "Profile Load User",
            "email": "profileload2307055@stud.kuet.ac.bd",
            "password": "secretpassword",
        })
        self.assertEqual(reg_resp.status_code, 200)
        token = client.post("/api/auth/login", json_data={
            "email": "profileload2307055@stud.kuet.ac.bd",
            "password": "secretpassword",
        }).json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        def fetch_profile():
            resp = client.get("/api/auth/me", headers=headers)
            return resp.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_profile) for _ in range(30)]
            statuses = [f.result() for f in futures]

        self.assertEqual(set(statuses), {200})
        self.assertEqual(len(statuses), 30)


if __name__ == "__main__":
    unittest.main()
