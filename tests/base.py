"""
Base Test Case for KUET CampusShare E2E Tests.
Provides isolated in-memory SQLite database, ASGI client, authentication helpers, and teardown.
"""

import os
import sys
import unittest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend directory is importable
repo_root = Path(__file__).resolve().parent.parent
backend_dir = repo_root / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app import database, models, auth
from tests.asgi_client import ASGIClient


class BaseE2ETestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app

    def setUp(self):
        # Create a completely fresh in-memory SQLite database for every test
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

    # --- Helper methods for fast, reproducible student actions ---

    def register_user(
        self,
        name: str = "Test Student",
        email: str = "tanvir2107001@stud.kuet.ac.bd",
        password: str = "password123",
    ):
        """Registers a student and returns the Response object."""
        return self.client.post(
            "/api/auth/register",
            json_data={"name": name, "email": email, "password": password},
        )

    def login_user(
        self,
        email: str = "tanvir2107001@stud.kuet.ac.bd",
        password: str = "password123",
    ):
        """Logs in a student and returns the Response object."""
        return self.client.post(
            "/api/auth/login",
            json_data={"email": email, "password": password},
        )

    def register_and_login(
        self,
        name: str = "Student",
        email: str = "student2107001@stud.kuet.ac.bd",
        password: str = "password123",
    ):
        """Registers, logs in, and returns (user_data, token, auth_headers)."""
        reg_resp = self.register_user(name=name, email=email, password=password)
        self.assertEqual(reg_resp.status_code, 200, f"Registration failed: {reg_resp.text}")
        user_data = reg_resp.json()

        login_resp = self.login_user(email=email, password=password)
        self.assertEqual(login_resp.status_code, 200, f"Login failed: {login_resp.text}")
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        return user_data, token, headers

    def create_item(
        self,
        auth_headers: dict,
        title: str = "Digital Multimeter",
        category: str = "Electronics",
        item_type: str = "lend",
        type: str = None,
        specs: str = "True RMS, CAT III",
        condition: str = "Like New",
        zone: str = "cse_bldg",
        latitude: float = 22.9003,
        longitude: float = 89.5024,
        description: str = "Multimeter for electronics lab work",
        tags: list = None,
    ):
        """Creates an item via the API using authenticated headers."""
        resolved_type = type or item_type or "lend"
        tags = tags or ["#Lab", "#Electronics"]
        payload = {
            "title": title,
            "category": category,
            "type": resolved_type,
            "specs": specs,
            "condition": condition,
            "zone": zone,
            "latitude": latitude,
            "longitude": longitude,
            "description": description,
            "tags": tags,
        }
        resp = self.client.post("/api/items", json_data=payload, headers=auth_headers)
        self.assertEqual(resp.status_code, 201, f"Item creation failed: {resp.text}")
        return resp.json()["item"]

    def create_borrow_request(
        self,
        auth_headers: dict,
        item_id: int,
        duration_hours: int = 24,
        purpose: str = "Lab experiment",
        pickup_zone: str = "cse_bldg",
        message: str = "Need for CSE 3100 lab",
    ):
        """Creates a borrow request via the API."""
        payload = {
            "item_id": item_id,
            "duration_hours": duration_hours,
            "purpose": purpose,
            "pickup_zone": pickup_zone,
            "message": message,
        }
        resp = self.client.post("/api/requests", json_data=payload, headers=auth_headers)
        return resp
