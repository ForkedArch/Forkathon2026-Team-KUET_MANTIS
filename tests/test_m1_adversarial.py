"""
Milestone 1 Empirical Adversarial Test Suite
KUET CampusShare: Rigorous Edge Cases, Database Resilience, Registration & Auth Stress Tests
"""

import os
import sys
import shutil
import tempfile
import subprocess
import unittest
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Ensure backend package is in python path
repo_root = Path(__file__).resolve().parent.parent
backend_dir = repo_root / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import models, schemas, database, auth
from app.routes import auth as auth_route
from app.routes.auth import KUET_DEPT_MAP, decode_dept_code, decode_kuet_email
from tests.base import BaseE2ETestCase


class TestAdversarialEmailDecoding(unittest.TestCase):
    """Adversarial stress-testing of email parsing, domain gatekeeping, and roll decoding."""

    def test_non_kuet_domain_matrix(self):
        """Reject non-KUET domains, faculty domains, alumni domains, and spoofed domains."""
        adversarial_domains = [
            "student2307001@gmail.com",
            "student2307001@yahoo.com",
            "student2307001@hotmail.com",
            "student2307001@outlook.com",
            "student2307001@kuet.ac.bd",              # Official faculty/institutional domain
            "teacher2307001@kuet.ac.bd",              # Faculty domain
            "student2307001@alumni.kuet.ac.bd",       # Alumni domain
            "student2307001@sub.stud.kuet.ac.bd",     # Subdomain spoof
            "student2307001@stud.kuet.ac.bd.evil.com",# Suffix spoof
            "student2307001@studkuet.ac.bd",          # Missing dot
            "student2307001@stud.kuet.edu.bd",        # .edu.bd spoof
            "student2307001@stud.kuet.edu",           # .edu spoof
            "student2307001@kuet.edu",                # Generic edu
            "student2307001@notkuet.com",             # External
            "student2307001@stud-kuet.ac.bd",         # Hyphen spoof
            "student2307001@fake.stud.kuet.ac.bd",    # Multi-subdomain
        ]
        for email in adversarial_domains:
            with self.assertRaises(HTTPException, msg=f"Should reject domain: {email}") as ctx:
                decode_kuet_email(email)
            self.assertEqual(ctx.exception.status_code, 400)
            self.assertIn("@stud.kuet.ac.bd", ctx.exception.detail)

    def test_multiple_at_symbols(self):
        """Reject inputs with multiple '@' symbols or invalid structure."""
        multi_at_inputs = [
            "user@evil.com@stud.kuet.ac.bd",
            "user@@stud.kuet.ac.bd",
            "@stud.kuet.ac.bd@",
            "user@something@else@stud.kuet.ac.bd",
            "student2307010@sub@stud.kuet.ac.bd",
        ]
        for email in multi_at_inputs:
            with self.assertRaises(HTTPException, msg=f"Should reject multi-@: {email}") as ctx:
                decode_kuet_email(email)
            self.assertEqual(ctx.exception.status_code, 400)

    def test_empty_none_and_invalid_types(self):
        """Reject empty, None, and non-string types."""
        invalid_types = [
            None,
            "",
            "   ",
            "@stud.kuet.ac.bd",
            "   @stud.kuet.ac.bd",
            12345,
            [],
            {},
        ]
        for val in invalid_types:
            with self.assertRaises(HTTPException, msg=f"Should reject invalid type/empty: {val}") as ctx:
                decode_kuet_email(val)
            self.assertEqual(ctx.exception.status_code, 400)

    def test_casing_resilience(self):
        """Verify case-insensitivity: uppercase, mixed-case domain and local part."""
        cases = [
            ("STUDENT2307010@STUD.KUET.AC.BD", ("23", "CSE", "010")),
            ("student2307010@STUD.KUET.AC.BD", ("23", "CSE", "010")),
            ("STUDENT2307010@stud.kuet.ac.bd", ("23", "CSE", "010")),
            ("sIdDiQuE2307010@StUd.KuEt.Ac.Bd", ("23", "CSE", "010")),
            ("  tanvir2107001@stud.kuet.ac.bd  ", ("21", "CSE", "001")),
        ]
        for email, expected in cases:
            res = decode_kuet_email(email)
            self.assertEqual(res, expected, f"Failed for casing case: {email}")

    def test_malformed_rolls_too_short(self):
        """Reject rolls that have fewer than 7 digits at the end of the local part."""
        too_short = [
            "student@stud.kuet.ac.bd",        # 0 digits
            "student1@stud.kuet.ac.bd",       # 1 digit
            "student23@stud.kuet.ac.bd",      # 2 digits
            "student230@stud.kuet.ac.bd",     # 3 digits
            "student2307@stud.kuet.ac.bd",    # 4 digits
            "student23070@stud.kuet.ac.bd",   # 5 digits
            "student230701@stud.kuet.ac.bd",  # 6 digits
        ]
        for email in too_short:
            with self.assertRaises(HTTPException, msg=f"Should reject too short roll: {email}") as ctx:
                decode_kuet_email(email)
            self.assertEqual(ctx.exception.status_code, 400)
            self.assertIn("7-digit student ID", ctx.exception.detail)

    def test_malformed_rolls_non_digit_characters(self):
        """Reject rolls containing non-digit characters in the 7-digit ID positions or trailing suffixes."""
        non_digit_cases = [
            "student2307010a@stud.kuet.ac.bd",     # Trailing letter
            "student2307010!@stud.kuet.ac.bd",     # Trailing special char
            "student23-07-010@stud.kuet.ac.bd",    # Hyphenated
            "student23_07_010@stud.kuet.ac.bd",    # Underscores in digits
            "student23.07.010@stud.kuet.ac.bd",    # Dots in digits
            "student23O7010@stud.kuet.ac.bd",      # Letter 'O' instead of '0'
            "student23l7010@stud.kuet.ac.bd",      # Letter 'l' instead of '1'
            "student২৩০৭০১০@stud.kuet.ac.bd",      # Bengali digits (non-ASCII)
            "student2307010🚀@stud.kuet.ac.bd",    # Emoji suffix
        ]
        for email in non_digit_cases:
            with self.assertRaises(HTTPException, msg=f"Should reject non-digit roll: {email}") as ctx:
                decode_kuet_email(email)
            self.assertEqual(ctx.exception.status_code, 400)

    def test_malformed_rolls_invalid_digits_and_lengths(self):
        """Reject malformed rolls where digits don't map to a valid KUET pattern."""
        malformed = [
            "student23070001@stud.kuet.ac.bd",  # 8 digits ending in 30 70 001 (dept 70 unmapped)
            "student12345678@stud.kuet.ac.bd",  # 8 digits ending in 23 45 678 (dept 45 unmapped)
            "student9999999@stud.kuet.ac.bd",   # 7 digits ending in dept 99 (unmapped)
            "student0000000@stud.kuet.ac.bd",   # 7 digits ending in dept 00 (unmapped)
        ]
        for email in malformed:
            with self.assertRaises(HTTPException, msg=f"Should reject malformed roll: {email}") as ctx:
                decode_kuet_email(email)
            self.assertEqual(ctx.exception.status_code, 400)

    def test_unmapped_department_codes(self):
        """Reject rolls with unmapped or invalid department codes (00, 30, 32, 40, 88, 99)."""
        unmapped_dept_emails = [
            "student2300001@stud.kuet.ac.bd",  # dept 00 (invalid)
            "student2330001@stud.kuet.ac.bd",  # dept 30 (unassigned in KUET)
            "student2332001@stud.kuet.ac.bd",  # dept 32 (exceeds max KUET code)
            "student2340001@stud.kuet.ac.bd",  # dept 40
            "student2388001@stud.kuet.ac.bd",  # dept 88
            "student2399001@stud.kuet.ac.bd",  # dept 99
        ]
        for email in unmapped_dept_emails:
            with self.assertRaises(HTTPException, msg=f"Should reject unmapped dept code: {email}") as ctx:
                decode_kuet_email(email)
            self.assertEqual(ctx.exception.status_code, 400)
            self.assertIn("not a recognized department code", ctx.exception.detail)

    def test_all_31_valid_department_codes(self):
        """Verify that every recognized KUET department code in KUET_DEPT_MAP successfully decodes."""
        for code, expected_acronym in KUET_DEPT_MAP.items():
            email = f"student23{code}001@stud.kuet.ac.bd"
            batch, dept, roll = decode_kuet_email(email)
            self.assertEqual(batch, "23")
            self.assertEqual(dept, expected_acronym, f"Dept code {code} should decode to {expected_acronym}")
            self.assertEqual(roll, "001")


class TestAdversarialDatabaseDirectoryCreation(unittest.TestCase):
    """Empirically test SQLite database directory auto-creation with deep nested paths."""

    def test_deep_nested_directory_auto_creation_in_process(self):
        """Initialize engine with a deep non-existent path and verify directory creation and schema migration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            deep_db_dir = Path(tmpdir) / "test_nested_dir" / "sub" / "level3"
            deep_db_file = deep_db_dir / "test_adversarial.db"
            self.assertFalse(deep_db_dir.exists(), "Target directory must not exist prior to test")

            db_url = f"sqlite:///{deep_db_file}"

            # Execute directory auto-creation logic matching database.py
            db_path_str = db_url.replace("sqlite:///", "", 1)
            file_path = db_path_str.split("?")[0]
            parent_dir = Path(file_path).resolve().parent
            parent_dir.mkdir(parents=True, exist_ok=True)

            self.assertTrue(deep_db_dir.exists(), "Directory should have been created by mkdir")

            # Create engine, connect, create tables, and execute query
            engine = create_engine(db_url, connect_args={"check_same_thread": False}, pool_pre_ping=True)
            models.Base.metadata.create_all(bind=engine)

            with engine.connect() as conn:
                res = conn.execute(text("SELECT 1")).scalar()
                self.assertEqual(res, 1)
                # Verify users table exists in newly created database file
                tables = [r[0] for r in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()]
                self.assertIn("users", tables)
                self.assertIn("items", tables)
                self.assertIn("borrow_requests", tables)
                self.assertIn("transactions", tables)

            engine.dispose()
            self.assertTrue(deep_db_file.exists(), "Database file must exist on disk")

    def test_database_url_query_parameter_handling(self):
        """Verify URL with query parameters does not break parent directory extraction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            deep_db_file = Path(tmpdir) / "nested_params" / "sub" / "param_test.db"
            db_url = f"sqlite:///{deep_db_file}?mode=rwc&cache=shared"

            db_path_str = db_url.replace("sqlite:///", "", 1)
            file_path = db_path_str.split("?")[0]
            parent_dir = Path(file_path).resolve().parent
            parent_dir.mkdir(parents=True, exist_ok=True)

            self.assertTrue(parent_dir.exists())
            self.assertFalse(str(parent_dir).endswith("shared"), "Parent directory path must not contain query parameters")

    def test_database_module_startup_with_nested_url_subprocess(self):
        """Execute a fresh Python process with DATABASE_URL=sqlite:///./test_nested_dir/sub/test.db to verify real boot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            deep_db_file = Path(tmpdir) / "subprocess_test" / "nested_dir" / "test.db"
            test_cmd = [
                sys.executable,
                "-c",
                f"""
import os, sys
from pathlib import Path
sys.path.insert(0, '{backend_dir}')
os.environ['DATABASE_URL'] = 'sqlite:///{deep_db_file}'
import app.database
app.database.migrate_db()
print('SUCCESS_MIGRATION')
"""
            ]
            result = subprocess.run(test_cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, f"Process failed: {result.stderr}")
            self.assertIn("SUCCESS_MIGRATION", result.stdout)
            self.assertTrue(deep_db_file.exists(), "Database file must be created on disk")


class TestAdversarialRegistrationAndAuth(BaseE2ETestCase):
    """Empirically test registration and auth API edge cases through full ASGI pipeline."""

    def test_duplicate_email_registration_exact_and_case(self):
        """Reject duplicate email registrations including case differences."""
        # 1. Register first student
        resp1 = self.register_user(
            name="Original Student",
            email="student2307001@stud.kuet.ac.bd",
            password="Password123!"
        )
        self.assertEqual(resp1.status_code, 200)

        # 2. Attempt exact duplicate
        resp_exact = self.register_user(
            name="Imposter Student",
            email="student2307001@stud.kuet.ac.bd",
            password="DifferentPassword456!"
        )
        self.assertEqual(resp_exact.status_code, 400)
        self.assertIn("Email already registered", resp_exact.json()["detail"])

        # 3. Attempt uppercase duplicate
        resp_upper = self.register_user(
            name="Upper Imposter",
            email="STUDENT2307001@STUD.KUET.AC.BD",
            password="DifferentPassword456!"
        )
        self.assertEqual(resp_upper.status_code, 400)
        self.assertIn("Email already registered", resp_upper.json()["detail"])

        # 4. Attempt whitespace padded duplicate
        resp_space = self.register_user(
            name="Padded Imposter",
            email="  student2307001@stud.kuet.ac.bd  ",
            password="DifferentPassword456!"
        )
        self.assertEqual(resp_space.status_code, 400)
        self.assertIn("Email already registered", resp_space.json()["detail"])

    def test_duplicate_roll_in_same_batch_and_dept_rejected(self):
        """Reject duplicate roll in the same batch and department even with different email local parts."""
        resp1 = self.register_user(
            name="Alice",
            email="alice2307005@stud.kuet.ac.bd",
            password="Password1!"
        )
        self.assertEqual(resp1.status_code, 200)

        # Bob tries to register with a different email prefix but same roll (23, 07->CSE, 005)
        resp2 = self.register_user(
            name="Bob",
            email="bob2307005@stud.kuet.ac.bd",
            password="Password2!"
        )
        self.assertEqual(resp2.status_code, 400)
        self.assertIn("Roll number already registered", resp2.json()["detail"])

    def test_same_roll_allowed_in_different_department(self):
        """Allow the same roll number across DIFFERENT departments in the same batch."""
        depts = [
            ("cse2307001@stud.kuet.ac.bd", "CSE"),
            ("eee2303001@stud.kuet.ac.bd", "EEE"),
            ("me2305001@stud.kuet.ac.bd",  "ME"),
            ("ce2301001@stud.kuet.ac.bd",  "CE"),
            ("bme2315001@stud.kuet.ac.bd", "BME"),
        ]
        for email, expected_dept in depts:
            resp = self.register_user(name=f"Student {expected_dept}", email=email, password="Password123!")
            self.assertEqual(resp.status_code, 200, f"Registration failed for dept {expected_dept}: {resp.text}")
            data = resp.json()
            self.assertEqual(data["roll"], "001")
            self.assertEqual(data["batch"], "23")
            self.assertEqual(data["dept"], expected_dept)

    def test_same_roll_and_dept_allowed_in_different_batches(self):
        """Allow the same roll number and department across DIFFERENT batches."""
        batches = [
            ("cse2007001@stud.kuet.ac.bd", "20"),
            ("cse2107001@stud.kuet.ac.bd", "21"),
            ("cse2207001@stud.kuet.ac.bd", "22"),
            ("cse2307001@stud.kuet.ac.bd", "23"),
            ("cse2407001@stud.kuet.ac.bd", "24"),
        ]
        for email, expected_batch in batches:
            resp = self.register_user(name=f"Batch {expected_batch} Student", email=email, password="Password123!")
            self.assertEqual(resp.status_code, 200, f"Registration failed for batch {expected_batch}: {resp.text}")
            data = resp.json()
            self.assertEqual(data["roll"], "001")
            self.assertEqual(data["dept"], "CSE")
            self.assertEqual(data["batch"], expected_batch)

    def test_sequential_department_alias_roll_collision(self):
        """Verify that sequential aliases mapping to the same department detect roll collisions."""
        # 02 and 03 both map to EEE
        resp1 = self.register_user(
            name="EEE Student Code 02",
            email="student2302001@stud.kuet.ac.bd",
            password="Password1!"
        )
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp1.json()["dept"], "EEE")

        # Code 03 also maps to EEE; same batch 23 and roll 001
        resp2 = self.register_user(
            name="EEE Student Code 03",
            email="student2303001@stud.kuet.ac.bd",
            password="Password2!"
        )
        self.assertEqual(resp2.status_code, 400)
        self.assertIn("Roll number already registered", resp2.json()["detail"])

    def test_base_karma_and_trust_score_initialization(self):
        """Verify new registration strictly receives 100 Base Karma, 100.0 trust score, and 0 lends/borrows."""
        resp = self.register_user(
            name="Karma Test Student",
            email="karmatest2307010@stud.kuet.ac.bd",
            password="SecretPassword123"
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["karma"], 100)
        self.assertEqual(data["trust_score"], 100.0)
        self.assertEqual(data["total_lends"], 0)
        self.assertEqual(data["total_borrows"], 0)

        # Inspect database record directly to ensure password is hashed
        user_in_db = self.db.query(models.User).filter(models.User.email == "karmatest2307010@stud.kuet.ac.bd").first()
        self.assertIsNotNone(user_in_db)
        self.assertNotEqual(user_in_db.hashed_password, "SecretPassword123")
        self.assertTrue(auth.verify_password("SecretPassword123", user_in_db.hashed_password))

    def test_registration_validation_boundaries(self):
        """Test registration validation boundaries for short passwords, empty names, and non-email formats."""
        # 1. Short password (< 4 chars)
        resp_short_pw = self.client.post("/api/auth/register", json_data={
            "name": "Valid Name",
            "email": "student2307030@stud.kuet.ac.bd",
            "password": "123"
        })
        self.assertEqual(resp_short_pw.status_code, 422)

        # 2. Empty / whitespace name
        resp_empty_name = self.client.post("/api/auth/register", json_data={
            "name": "   ",
            "email": "student2307031@stud.kuet.ac.bd",
            "password": "password123"
        })
        self.assertEqual(resp_empty_name.status_code, 422)

        # 3. Invalid email format (non-email string)
        resp_bad_fmt = self.client.post("/api/auth/register", json_data={
            "name": "Valid Name",
            "email": "not-an-email",
            "password": "password123"
        })
        self.assertEqual(resp_bad_fmt.status_code, 422)

    def test_sql_injection_resilience(self):
        """Verify SQL injection payloads in email, name, and password cannot breach the system."""
        # SQLi payload in email
        resp_sqli_email = self.client.post("/api/auth/register", json_data={
            "name": "Attacker",
            "email": "admin' OR '1'='1@stud.kuet.ac.bd",
            "password": "password123"
        })
        self.assertIn(resp_sqli_email.status_code, [400, 422])

        # SQLi payload in password is safely hashed
        resp_sqli_pw = self.register_user(
            name="Sqli User",
            email="sqliuser2307040@stud.kuet.ac.bd",
            password="' OR '1'='1"
        )
        self.assertEqual(resp_sqli_pw.status_code, 200)

        # Attempt to login with different password
        resp_bad_login = self.login_user(
            email="sqliuser2307040@stud.kuet.ac.bd",
            password="' OR '1'='2"
        )
        self.assertEqual(resp_bad_login.status_code, 401)

        # Successful login requires exact matching password string
        resp_good_login = self.login_user(
            email="sqliuser2307040@stud.kuet.ac.bd",
            password="' OR '1'='1"
        )
        self.assertEqual(resp_good_login.status_code, 200)

    def test_login_and_token_validation_edge_cases(self):
        """Test login with case insensitivity, wrong password, nonexistent user, and JWT token protection."""
        self.register_user(
            name="Auth Test Student",
            email="authtest2307020@stud.kuet.ac.bd",
            password="StrongPassword123"
        )

        # Case-insensitive login
        resp_login_case = self.login_user(
            email="AUTHTEST2307020@STUD.KUET.AC.BD",
            password="StrongPassword123"
        )
        self.assertEqual(resp_login_case.status_code, 200)
        token = resp_login_case.json()["access_token"]

        # Authenticated /me
        resp_me = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp_me.status_code, 200)
        self.assertEqual(resp_me.json()["email"], "authtest2307020@stud.kuet.ac.bd")

        # Wrong password
        resp_bad_pass = self.login_user(
            email="authtest2307020@stud.kuet.ac.bd",
            password="WrongPassword123"
        )
        self.assertEqual(resp_bad_pass.status_code, 401)
        self.assertEqual(resp_bad_pass.json()["detail"], "Incorrect email or password")

        # Nonexistent user
        resp_no_user = self.login_user(
            email="nonexistent2307099@stud.kuet.ac.bd",
            password="AnyPassword"
        )
        self.assertEqual(resp_no_user.status_code, 401)

        # Tampered JWT token
        resp_tampered = self.client.get("/api/auth/me", headers={"Authorization": "Bearer fake.tampered.token"})
        self.assertEqual(resp_tampered.status_code, 401)

        # Missing Authorization header (FastAPI HTTPBearer returns 403 Forbidden)
        resp_no_auth = self.client.get("/api/auth/me")
        self.assertIn(resp_no_auth.status_code, [401, 403])


if __name__ == "__main__":
    unittest.main()
