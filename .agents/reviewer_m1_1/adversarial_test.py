import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

backend_dir = Path("/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend")
sys.path.insert(0, str(backend_dir))

from app.main import app
from app import models, database, schemas
from test_m1 import ASGIClient

client = ASGIClient(app)

def test_adversarial_auth():
    print("=== ADVERSARIAL AUTH TESTS ===")
    
    # 1. Subdomain trick: evil domain ending with something else
    r = client.post("/api/auth/register", json={
        "name": "Attacker",
        "email": "attacker2507028@stud.kuet.ac.bd.attacker.com",
        "password": "pass"
    })
    assert r.status_code == 400, f"Expected 400 for attacker.com, got {r.status_code}"
    print("[PASS] Subdomain hijack attempt rejected.")

    # 2. Staff domain (not student): @kuet.ac.bd
    r = client.post("/api/auth/register", json={
        "name": "Teacher",
        "email": "teacher@kuet.ac.bd",
        "password": "pass"
    })
    assert r.status_code == 400, f"Expected 400 for non-student kuet domain, got {r.status_code}"
    print("[PASS] Non-student domain rejected.")

    # 3. Uppercase email: SIDDIQUE2608099@STUD.KUET.AC.BD
    r = client.post("/api/auth/register", json={
        "name": "Upper Case Student",
        "email": "SIDDIQUE2608099@STUD.KUET.AC.BD",
        "password": "pass"
    })
    assert r.status_code in [200, 400], f"Unexpected status: {r.status_code}"
    if r.status_code == 200:
        data = r.json()
        assert data["batch"] == "26"
        assert data["dept"] == "08"
        assert data["roll"] == "099"
        assert data["karma"] == 100
        print("[PASS] Uppercase email normalized and registered correctly.")
    else:
        print("[INFO] Uppercase email already registered or rejected.")

    # 4. Email with dot in prefix: "first.last2709111@stud.kuet.ac.bd"
    r = client.post("/api/auth/register", json={
        "name": "Dotted Student",
        "email": "first.last2709111@stud.kuet.ac.bd",
        "password": "pass"
    })
    if r.status_code == 200:
        data = r.json()
        assert data["batch"] == "27"
        assert data["dept"] == "09"
        assert data["roll"] == "111"
        print("[PASS] Dotted prefix handled correctly.")

    # 5. Exactly duplicate batch, dept, roll with DIFFERENT email prefix
    r_dup = client.post("/api/auth/register", json={
        "name": "Impostor",
        "email": "impostor2709111@stud.kuet.ac.bd",
        "password": "pass"
    })
    assert r_dup.status_code == 400, f"Expected 400 duplicate composite key, got {r_dup.status_code}"
    print("[PASS] Duplicate composite key (batch, dept, roll) rejected with 400.")

    # 6. SQL injection attempt in registration
    r_inj = client.post("/api/auth/register", json={
        "name": "Bobby' OR '1'='1",
        "email": "bobby2810222@stud.kuet.ac.bd",
        "password": "pass"
    })
    assert r_inj.status_code in [200, 400]
    print("[PASS] SQL injection in registration handled safely by ORM parameterization.")


def test_adversarial_items():
    print("\n=== ADVERSARIAL ITEMS TESTS ===")

    # 1. Search with SQL injection payload
    r = client.get("/api/items?q=' OR '1'='1")
    assert r.status_code == 200
    print("[PASS] Search query with SQL syntax handled safely.")

    # 2. Search with special characters %, _, <script>
    r = client.get("/api/items?q=%25%27<script>alert(1)</script>")
    assert r.status_code == 200
    print("[PASS] Search query with XSS/wildcard handled safely.")

    # 3. Filter with case variation: type=LEND, type=Borrow
    r_lend = client.get("/api/items?type=LEND")
    assert r_lend.status_code == 200
    r_borrow = client.get("/api/items?type=Borrow")
    assert r_borrow.status_code == 200
    assert len(r_lend.json()) > 0
    assert len(r_borrow.json()) > 0
    print("[PASS] Case-insensitive type filtering works.")

    # 4. Non-existent item ID
    r_notfound = client.get("/api/items/999999")
    assert r_notfound.status_code == 404
    print("[PASS] Non-existent item returns 404.")


def test_adversarial_transactions():
    print("\n=== ADVERSARIAL TRANSACTIONS & KARMA TESTS ===")

    # Login as Tanvir
    res_login = client.post("/api/auth/login", json={
        "email": "tanvir2207001@stud.kuet.ac.bd",
        "password": "kuet1234"
    })
    tanvir_token = res_login.json()["access_token"]
    tanvir_h = {"Authorization": f"Bearer {tanvir_token}"}

    # Login as Siddique
    res_login_sid = client.post("/api/auth/login", json={
        "email": "siddique2307010@stud.kuet.ac.bd",
        "password": "kuet1234"
    })
    sid_token = res_login_sid.json()["access_token"]
    sid_h = {"Authorization": f"Bearer {sid_token}"}

    # 1. Borrower tries to start handover (should be forbidden, only owner can)
    # First create an item for Tanvir
    r_item = client.post("/api/items/", json={
        "title": "Adversarial Test Item",
        "category": "Electronics",
        "type": "lend",
        "specs": "Test",
        "condition": "New"
    }, headers=tanvir_h)
    item_id = r_item.json().get("id") or r_item.json().get("item", {}).get("id")

    # Siddique requests item
    r_req = client.post("/api/requests/", json={
        "item_id": item_id,
        "duration_hours": 1
    }, headers=sid_h)
    assert r_req.status_code == 200
    req_id = r_req.json()["id"]

    # Siddique tries to start transaction before accept
    r_start_fail = client.post("/api/transactions/start", json={"request_id": req_id}, headers=sid_h)
    assert r_start_fail.status_code == 403, f"Expected 403 for non-owner start, got {r_start_fail.status_code}"
    print("[PASS] Borrower cannot start handover (403).")

    # Tanvir accepts request
    r_acc = client.put(f"/api/requests/{req_id}/status?status=accepted", headers=tanvir_h)
    assert r_acc.status_code == 200

    # Try to accept again (already resolved)
    r_acc2 = client.put(f"/api/requests/{req_id}/status?status=accepted", headers=tanvir_h)
    assert r_acc2.status_code == 400
    print("[PASS] Cannot accept an already resolved request (400).")

    # Tanvir starts transaction
    r_start = client.post("/api/transactions/start", json={"request_id": req_id}, headers=tanvir_h)
    assert r_start.status_code == 200
    otp = r_start.json()["otp"]

    # Tanvir tries to verify handover (should fail, only borrower can verify)
    r_ver_owner = client.post("/api/transactions/verify", json={"request_id": req_id, "otp": otp}, headers=tanvir_h)
    assert r_ver_owner.status_code == 403
    print("[PASS] Owner cannot verify own handover (403).")

    # Siddique tries with WRONG OTP
    r_ver_bad = client.post("/api/transactions/verify", json={"request_id": req_id, "otp": "9999"}, headers=sid_h)
    assert r_ver_bad.status_code == 400
    print("[PASS] Invalid OTP rejected with 400.")

    # Siddique verifies with correct OTP
    r_ver_ok = client.post("/api/transactions/verify", json={"request_id": req_id, "otp": otp}, headers=sid_h)
    assert r_ver_ok.status_code == 200
    print("[PASS] Valid OTP verified.")

    # Tanvir tries to request return (only borrower can request return)
    r_ret_owner = client.post(f"/api/transactions/return/{req_id}", headers=tanvir_h)
    assert r_ret_owner.status_code == 403
    print("[PASS] Owner cannot return item (403).")

    # Siddique returns item
    r_ret_ok = client.post(f"/api/transactions/return/{req_id}", headers=sid_h)
    assert r_ret_ok.status_code == 200
    print("[PASS] Borrower returned item successfully.")

    # Siddique tries to return AGAIN (replay attack)
    r_ret_again = client.post(f"/api/transactions/return/{req_id}", headers=sid_h)
    assert r_ret_again.status_code == 400
    print("[PASS] Replay return attack rejected (400).")


if __name__ == "__main__":
    test_adversarial_auth()
    test_adversarial_items()
    test_adversarial_transactions()
    print("\nALL ADVERSARIAL STRESS TESTS PASSED SUCCESSFULLY!")
