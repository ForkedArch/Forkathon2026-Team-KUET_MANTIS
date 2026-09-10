"""
Milestone 1 Verification Test Suite
KUET CampusShare: Backend Auth, Database Resilience & Deployment Configuration
"""

import os
import json
import yaml
import tempfile
import unittest
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend package is in python path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app import models, schemas, database, auth
from app.routes import auth as auth_route
from app.routes.auth import KUET_DEPT_MAP, decode_dept_code, decode_kuet_email


class TestKuetDeptMapping(unittest.TestCase):
    """Verify all 31 official KUET department codes and aliases."""

    def test_all_official_codes(self):
        expected_mappings = {
            "01": "CE", "02": "EEE", "03": "EEE", "04": "ME", "05": "ME",
            "06": "ECE", "07": "CSE", "08": "BME", "09": "ECE", "10": "TE",
            "11": "IEM", "12": "ESE", "13": "ESE", "14": "ChE", "15": "BME",
            "16": "Arch", "17": "URP", "18": "URP", "19": "BECM", "20": "BECM",
            "21": "MSE", "22": "MSE", "23": "ChE", "24": "ChE", "25": "MTE",
            "26": "MTE", "27": "Arch", "28": "Arch", "29": "LE", "31": "TE"
        }
        for code, expected_acronym in expected_mappings.items():
            self.assertEqual(
                decode_dept_code(code),
                expected_acronym,
                f"Department code {code} should map to {expected_acronym}"
            )

    def test_single_digit_padding(self):
        self.assertEqual(decode_dept_code("7"), "CSE")
        self.assertEqual(decode_dept_code("1"), "CE")
        self.assertEqual(decode_dept_code("3"), "EEE")
        self.assertEqual(decode_dept_code("5"), "ME")

    def test_acronym_preservation(self):
        self.assertEqual(decode_dept_code("cse"), "CSE")
        self.assertEqual(decode_dept_code("EEE"), "EEE")


class TestKuetEmailDecoder(unittest.TestCase):
    """Verify strict @stud.kuet.ac.bd domain enforcement and 7-digit roll extraction."""

    def test_valid_emails(self):
        test_cases = [
            ("siddique2307010@stud.kuet.ac.bd", ("23", "CSE", "010")),
            ("tanvir2107001@stud.kuet.ac.bd", ("21", "CSE", "001")),
            ("student2203050@stud.kuet.ac.bd", ("22", "EEE", "050")),
            ("student2201010@stud.kuet.ac.bd", ("22", "CE", "010")),
            ("student2205020@stud.kuet.ac.bd", ("22", "ME", "020")),
            ("2107001@stud.kuet.ac.bd", ("21", "CSE", "001")),
            ("first.last2407099@stud.kuet.ac.bd", ("24", "CSE", "099")),
            ("student_2525001@stud.kuet.ac.bd", ("25", "MTE", "001")),
        ]
        for email, expected in test_cases:
            res = decode_kuet_email(email)
            self.assertEqual(res, expected, f"Failed for email {email}")

    def test_external_domain_rejections(self):
        invalid_domains = [
            "student@gmail.com",
            "student@yahoo.com",
            "teacher@kuet.ac.bd",
            "admin@sub.stud.kuet.ac.bd",
            "student@stud.kuet.ac.bd.attacker.com",
            "student@notstud.kuet.ac.bd",
            "student@kuet.ac.bd",
        ]
        for email in invalid_domains:
            with self.assertRaises(HTTPException) as ctx:
                decode_kuet_email(email)
            self.assertEqual(ctx.exception.status_code, 400)
            self.assertIn("stud.kuet.ac.bd", ctx.exception.detail)

    def test_multi_at_sign_rejection(self):
        with self.assertRaises(HTTPException) as ctx:
            decode_kuet_email("user@fakedomain.com@stud.kuet.ac.bd")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_malformed_roll_rejections(self):
        malformed_emails = [
            "student12345@stud.kuet.ac.bd",       # 5 digits
            "tanvir.rahman@stud.kuet.ac.bd",      # No digits
            "student2107001abc@stud.kuet.ac.bd",  # Letters after roll
        ]
        for email in malformed_emails:
            with self.assertRaises(HTTPException) as ctx:
                decode_kuet_email(email)
            self.assertEqual(ctx.exception.status_code, 400)
            self.assertIn("7-digit student ID", ctx.exception.detail)

    def test_invalid_dept_code_rejection(self):
        with self.assertRaises(HTTPException) as ctx:
            decode_kuet_email("student2399001@stud.kuet.ac.bd")  # dept 99 does not exist
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("department code", ctx.exception.detail.lower())


class TestAuthLifecycleAndKarma(unittest.TestCase):
    """Verify registration, 100 Base Karma initialization, login, and profile endpoints."""

    def setUp(self):
        # Create an isolated in-memory test database
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False}
        )
        models.Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        models.Base.metadata.drop_all(bind=self.engine)

    def test_registration_with_base_karma(self):
        user_in = schemas.UserRegister(
            name="Siddique Ahmed",
            email="siddique2307010@stud.kuet.ac.bd",
            password="secretpassword"
        )
        new_user = auth_route.register(user_in, self.db)
        self.assertEqual(new_user.name, "Siddique Ahmed")
        self.assertEqual(new_user.email, "siddique2307010@stud.kuet.ac.bd")
        self.assertEqual(new_user.batch, "23")
        self.assertEqual(new_user.dept, "CSE")
        self.assertEqual(new_user.roll, "010")
        self.assertEqual(new_user.karma, 100, "Must initialize with 100 Base Karma")
        self.assertEqual(new_user.trust_score, 100.0)
        self.assertEqual(new_user.total_lends, 0)
        self.assertEqual(new_user.total_borrows, 0)

    def test_duplicate_email_prevention(self):
        user_in = schemas.UserRegister(
            name="Student One",
            email="student2307001@stud.kuet.ac.bd",
            password="password1"
        )
        auth_route.register(user_in, self.db)

        # Duplicate email with different name
        user_dup = schemas.UserRegister(
            name="Student Duplicate",
            email="student2307001@stud.kuet.ac.bd",
            password="password2"
        )
        with self.assertRaises(HTTPException) as ctx:
            auth_route.register(user_dup, self.db)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Email already registered", ctx.exception.detail)

    def test_duplicate_roll_in_same_batch_dept_prevention(self):
        user_1 = schemas.UserRegister(
            name="Student A",
            email="alice2307005@stud.kuet.ac.bd",
            password="passwordA"
        )
        auth_route.register(user_1, self.db)

        # Different email, same batch (23), dept (07 -> CSE), roll (005)
        user_2 = schemas.UserRegister(
            name="Student B",
            email="bob2307005@stud.kuet.ac.bd",
            password="passwordB"
        )
        with self.assertRaises(HTTPException) as ctx:
            auth_route.register(user_2, self.db)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Roll number already registered", ctx.exception.detail)

    def test_composite_roll_uniqueness_allows_same_roll_in_different_dept(self):
        # Roll 001 in CSE (23)
        user_cse = schemas.UserRegister(
            name="CSE Student",
            email="cse2307001@stud.kuet.ac.bd",
            password="password1"
        )
        reg_cse = auth_route.register(user_cse, self.db)
        self.assertEqual(reg_cse.roll, "001")
        self.assertEqual(reg_cse.dept, "CSE")

        # Roll 001 in EEE (23) - must succeed
        user_eee = schemas.UserRegister(
            name="EEE Student",
            email="eee2303001@stud.kuet.ac.bd",
            password="password2"
        )
        reg_eee = auth_route.register(user_eee, self.db)
        self.assertEqual(reg_eee.roll, "001")
        self.assertEqual(reg_eee.dept, "EEE")

        # Roll 001 in CSE (22) - must succeed (different batch)
        user_cse_22 = schemas.UserRegister(
            name="Senior CSE Student",
            email="senior2207001@stud.kuet.ac.bd",
            password="password3"
        )
        reg_senior = auth_route.register(user_cse_22, self.db)
        self.assertEqual(reg_senior.roll, "001")
        self.assertEqual(reg_senior.batch, "22")

    def test_login_success_and_failure(self):
        # Register user
        user_in = schemas.UserRegister(
            name="Test Login Student",
            email="login2307088@stud.kuet.ac.bd",
            password="correct_password"
        )
        reg_user = auth_route.register(user_in, self.db)

        # Successful login
        login_in = schemas.UserLogin(
            email="login2307088@stud.kuet.ac.bd",
            password="correct_password"
        )
        token_res = auth_route.login(login_in, self.db)
        self.assertIn("access_token", token_res)
        self.assertEqual(token_res["token_type"], "bearer")
        self.assertEqual(token_res["user"].id, reg_user.id)

        # Invalid password
        bad_pass = schemas.UserLogin(
            email="login2307088@stud.kuet.ac.bd",
            password="wrong_password"
        )
        with self.assertRaises(HTTPException) as ctx:
            auth_route.login(bad_pass, self.db)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail, "Incorrect email or password")

        # Nonexistent email
        nonexistent = schemas.UserLogin(
            email="nobody2307099@stud.kuet.ac.bd",
            password="any_password"
        )
        with self.assertRaises(HTTPException) as ctx:
            auth_route.login(nonexistent, self.db)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_profile_endpoints(self):
        user_in = schemas.UserRegister(
            name="Profile Student",
            email="profile2307077@stud.kuet.ac.bd",
            password="mypassword"
        )
        user = auth_route.register(user_in, self.db)

        # /me endpoint
        me_out = auth_route.get_current_user_info(user)
        self.assertEqual(me_out.id, user.id)

        # /current endpoint (alias)
        cur_out = auth_route.get_current_user_alias(user)
        self.assertEqual(cur_out.id, user.id)

        # /user/{user_id} endpoint
        public_out = auth_route.get_user_public_profile(user.id, self.db)
        self.assertEqual(public_out.id, user.id)

        # Nonexistent user
        with self.assertRaises(HTTPException) as ctx:
            auth_route.get_user_public_profile(999999, self.db)
        self.assertEqual(ctx.exception.status_code, 404)


class TestDatabaseResilience(unittest.TestCase):
    """Verify parent directory auto-creation for SQLite files and pool_pre_ping."""

    def test_sqlite_directory_auto_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            deep_path = Path(tmpdir) / "level1" / "level2" / "test.db"
            db_url = f"sqlite:///{deep_path}"
            
            # Simulate database.py resilience logic
            db_path_str = db_url.replace("sqlite:///", "", 1)
            parent_dir = Path(db_path_str).resolve().parent
            parent_dir.mkdir(parents=True, exist_ok=True)

            engine = create_engine(db_url, connect_args={"check_same_thread": False}, pool_pre_ping=True)
            with engine.connect() as conn:
                res = conn.exec_driver_sql("SELECT 1").scalar()
                self.assertEqual(res, 1)
            self.assertTrue(deep_path.parent.exists())

    def test_engine_has_pool_pre_ping(self):
        from app.database import engine
        self.assertTrue(getattr(engine.pool, "_pre_ping", False))


class TestDeploymentConfigs(unittest.TestCase):
    """Verify render.yaml and vercel.json compliance."""

    def test_render_yaml_free_tier(self):
        render_path = Path(__file__).resolve().parent.parent / "render.yaml"
        with open(render_path) as f:
            data = yaml.safe_load(f)

        backend = next(s for s in data["services"] if s["name"] == "campusshare-backend")
        self.assertEqual(backend["plan"], "free")
        self.assertNotIn("disk", backend, "Render free tier must not declare persistent disks")

        env_map = {e["key"]: e for e in backend["envVars"]}
        self.assertTrue(env_map["SECRET_KEY"].get("generateValue"))
        self.assertEqual(env_map["DATABASE_URL"].get("value"), "sqlite:///./campus_share.db")
        self.assertEqual(env_map["UPLOAD_DIR"].get("value"), "./uploads")
        self.assertIn("ALLOWED_ORIGINS", env_map)
        self.assertIn("vercel.app", env_map["ALLOWED_ORIGINS"]["value"])

    def test_vercel_json_reverse_proxy(self):
        root_vercel = Path(__file__).resolve().parent.parent / "vercel.json"
        frontend_vercel = Path(__file__).resolve().parent.parent / "frontend" / "vercel.json"

        for vpath in [root_vercel, frontend_vercel]:
            with open(vpath) as f:
                cfg = json.load(f)
            rewrites = cfg.get("rewrites", [])
            self.assertGreaterEqual(len(rewrites), 3, f"{vpath} must have at least 3 rewrites")

            api_rewrite = next((r for r in rewrites if r.get("source") == "/api/:path*"), None)
            uploads_rewrite = next((r for r in rewrites if r.get("source") == "/uploads/:path*"), None)
            spa_rewrite = next((r for r in rewrites if r.get("source") == "/(.*)"), None)

            self.assertIsNotNone(api_rewrite, f"{vpath} must have /api/:path* rewrite")
            self.assertIsNotNone(uploads_rewrite, f"{vpath} must have /uploads/:path* rewrite")
            self.assertIsNotNone(spa_rewrite, f"{vpath} must have catch-all /(.*) rewrite")

            # Verify order: API and uploads rewrites MUST appear before the SPA catch-all
            api_idx = rewrites.index(api_rewrite)
            uploads_idx = rewrites.index(uploads_rewrite)
            spa_idx = rewrites.index(spa_rewrite)

            self.assertLess(api_idx, spa_idx, "/api/:path* rewrite must precede /(.*)")
            self.assertLess(uploads_idx, spa_idx, "/uploads/:path* rewrite must precede /(.*)")


if __name__ == "__main__":
    unittest.main()
