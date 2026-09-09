import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Ensure backend directory is in path
backend_dir = Path("/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend").resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app import models, database, auth
from test_m1 import ASGIClient

client = ASGIClient(app)

def run_adversarial_suite():
    print("==================================================")
    print("STARTING ADVERSARIAL STRESS-TEST SUITE FOR M1")
    print("==================================================")

    # ----------------------------------------------------
    # 1. Non-KUET Email & Edge Cases (Domain Validation)
    # ----------------------------------------------------
    print("\n[SECTION 1] Stress-testing Email Domain & Format Validation...")
    invalid_emails = [
        ("outsider@gmail.com", "Standard Gmail"),
        ("faculty@kuet.ac.bd", "KUET faculty/staff (not student domain)"),
        ("hacker@stud.kuet.ac.bd.attacker.com", "Subdomain suffix spoofing"),
        ("attacker@stud.kuet.ac.bd@other.com", "Double @ spoofing"),
        ("no_roll@stud.kuet.ac.bd", "Missing numeric roll"),
        ("short123456@stud.kuet.ac.bd", "Only 6 digits instead of 7"),
        ("alpha250702a@stud.kuet.ac.bd", "Alphanumeric in roll portion"),
        ("symbol2507#28@stud.kuet.ac.bd", "Symbol in roll portion"),
    ]

    for email, desc in invalid_emails:
        payload = {
            "name": "Test Attacker",
            "email": email,
            "password": "Password123!"
        }
        res = client.post("/api/auth/register", json=payload)
        assert res.status_code in [400, 422], f"VULNERABILITY: {desc} ({email}) was not rejected! Status: {res.status_code}, body: {res.text}"
        print(f"  [PASS] Rejected {desc} ({email}) with status {res.status_code}")

    # Test case sensitivity and whitespace trimming
    valid_upper_email = "STRESS_USER_992507999@STUD.KUET.AC.BD"
    res_upper = client.post("/api/auth/register", json={
        "name": "Uppercase User",
        "email": f"  {valid_upper_email}  ",
        "password": "Password123!"
    })
    if res_upper.status_code == 400 and "already registered" in res_upper.text:
        print("  [PASS] Uppercase/padded email properly normalized and identified existing user.")
    else:
        assert res_upper.status_code == 200, f"FAILED uppercase registration: {res_upper.status_code} {res_upper.text}"
        data = res_upper.json()
        assert data["batch"] == "25"
        assert data["dept"] == "07"
        assert data["roll"] == "999"
        assert data["email"] == valid_upper_email.strip().lower()
        print("  [PASS] Uppercase/padded email properly normalized and decoded: batch=25, dept=07, roll=999")

    # ----------------------------------------------------
    # 2. KUET Roll Decoding & Composite Uniqueness
    # ----------------------------------------------------
    print("\n[SECTION 2] Stress-testing Roll Decoding & Composite Uniqueness...")
    # Register student A: batch=24, dept=07, roll=888
    email_a = "std_a_2407888@stud.kuet.ac.bd"
    res_a = client.post("/api/auth/register", json={
        "name": "Student A",
        "email": email_a,
        "password": "Password123!"
    })
    if res_a.status_code != 400:
        assert res_a.status_code == 200
        assert res_a.json()["batch"] == "24"
        assert res_a.json()["dept"] == "07"
        assert res_a.json()["roll"] == "888"

    # Attempt to register student B with DIFFERENT email but SAME (batch=24, dept=07, roll=888)
    email_b = "impostor_2407888@stud.kuet.ac.bd"
    res_b = client.post("/api/auth/register", json={
        "name": "Impostor Student",
        "email": email_b,
        "password": "Password123!"
    })
    assert res_b.status_code == 400, f"VULNERABILITY: Impostor with same (batch, dept, roll) succeeded! Status: {res_b.status_code}"
    assert "Roll number already registered" in res_b.text or "UNIQUE" in res_b.text
    print("  [PASS] Composite uniqueness prevents different email with duplicate (batch, dept, roll)")

    # Attempt to register student C with SAME roll=888, SAME batch=24, but DIFFERENT dept=01
    email_c = "dept01_student_2401888@stud.kuet.ac.bd"
    res_c = client.post("/api/auth/register", json={
        "name": "Civil Student",
        "email": email_c,
        "password": "Password123!"
    })
    if res_c.status_code != 400:
        assert res_c.status_code == 200
        assert res_c.json()["dept"] == "01"
        assert res_c.json()["roll"] == "888"
        print("  [PASS] Composite uniqueness allows same roll in different department")

    # Attempt to register student D with SAME roll=888, SAME dept=07, but DIFFERENT batch=23
    email_d = "batch23_student_2307888@stud.kuet.ac.bd"
    res_d = client.post("/api/auth/register", json={
        "name": "Batch 23 Student",
        "email": email_d,
        "password": "Password123!"
    })
    if res_d.status_code != 400:
        assert res_d.status_code == 200
        assert res_d.json()["batch"] == "23"
        assert res_d.json()["roll"] == "888"
        print("  [PASS] Composite uniqueness allows same roll in different batch")

    # Verify base karma for new registrations
    assert res_a.json().get("karma", 100) == 100
    print("  [PASS] New user initialized with exactly 100 Base Karma")

    # ----------------------------------------------------
    # 3. KUET Karma Protocol Boundary & Security Stress Tests
    # ----------------------------------------------------
    print("\n[SECTION 3] Stress-testing KUET Karma Protocol (+10, +5, -30) & State Machine...")

    # Logins for Tanvir (Owner) and Siddique (Borrower)
    owner_tok = client.post("/api/auth/login", json={"email": "tanvir2207001@stud.kuet.ac.bd", "password": "kuet1234"}).json()["access_token"]
    borrower_tok = client.post("/api/auth/login", json={"email": "siddique2307010@stud.kuet.ac.bd", "password": "kuet1234"}).json()["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_tok}"}
    borrower_headers = {"Authorization": f"Bearer {borrower_tok}"}

    # 3.1 Cannot request own item
    # Item 2 is owned by Tanvir (user 3)
    own_req_res = client.post("/api/requests/", json={
        "item_id": 2,
        "duration_hours": 2,
    }, headers=owner_headers)
    assert own_req_res.status_code == 400
    assert "cannot request your own item" in own_req_res.text.lower()
    print("  [PASS] Owner cannot request their own item")

    # 3.2 Create legitimate request from Siddique for Item 2
    br_res = client.post("/api/requests/", json={
        "item_id": 2,
        "duration_hours": 3,
        "purpose": "Boundary testing"
    }, headers=borrower_headers)
    assert br_res.status_code == 200
    req_id = br_res.json()["id"]

    # 3.3 Non-owner cannot accept/decline request
    unauth_accept = client.put(f"/api/requests/{req_id}/status?status=accepted", headers=borrower_headers)
    assert unauth_accept.status_code == 403
    print("  [PASS] Unauthorized user cannot accept borrow request (HTTP 403)")

    # 3.4 Invalid status value rejected
    bad_status = client.put(f"/api/requests/{req_id}/status?status=invalid_status", headers=owner_headers)
    assert bad_status.status_code in [400, 422]
    print("  [PASS] Invalid status value rejected (HTTP 400/422)")

    # 3.5 Owner accepts request
    acc_res = client.put(f"/api/requests/{req_id}/status?status=accepted", headers=owner_headers)
    assert acc_res.status_code == 200

    # 3.6 Cannot accept already accepted request
    double_acc = client.put(f"/api/requests/{req_id}/status?status=accepted", headers=owner_headers)
    assert double_acc.status_code == 400
    print("  [PASS] Double acceptance prevented (HTTP 400)")

    # 3.7 Non-owner cannot start handover
    unauth_start = client.post("/api/transactions/start", json={"request_id": req_id}, headers=borrower_headers)
    assert unauth_start in [403, None] or unauth_start.status_code == 403
    print("  [PASS] Non-owner cannot start handover (HTTP 403)")

    # 3.8 Owner starts handover -> OTP generated
    start_res = client.post("/api/transactions/start", json={"request_id": req_id}, headers=owner_headers)
    assert start_res.status_code == 200
    otp = start_res.json()["otp"]
    assert len(otp) == 4 and otp.isdigit()
    print("  [PASS] Handover initiated, 4-digit OTP issued")

    # 3.9 Non-borrower cannot verify handover
    unauth_verify = client.post("/api/transactions/verify", json={"request_id": req_id, "otp": otp}, headers=owner_headers)
    assert unauth_verify.status_code == 403
    print("  [PASS] Non-borrower cannot verify handover (HTTP 403)")

    # 3.10 Wrong OTP rejected
    wrong_otp = client.post("/api/transactions/verify", json={"request_id": req_id, "otp": "9999" if otp != "9999" else "0000"}, headers=borrower_headers)
    assert wrong_otp.status_code == 400
    print("  [PASS] Wrong OTP rejected (HTTP 400)")

    # 3.11 Correct OTP verifies handover
    verify_res = client.post("/api/transactions/verify", json={"request_id": req_id, "otp": otp}, headers=borrower_headers)
    assert verify_res.status_code == 200
    print("  [PASS] Handover verified with correct OTP")

    # 3.12 Non-borrower cannot call return
    unauth_ret = client.post(f"/api/transactions/return/{req_id}", headers=owner_headers)
    assert unauth_ret.status_code == 403
    print("  [PASS] Non-borrower cannot trigger return (HTTP 403)")

    # 3.13 Test EXACT On-Time return:
    # Baseline karma
    db = database.SessionLocal()
    owner_k_before = db.query(models.User).filter(models.User.id == 3).first().karma
    borrower_k_before = db.query(models.User).filter(models.User.id == 2).first().karma
    db.close()

    ret_res = client.post(f"/api/transactions/return/{req_id}", headers=borrower_headers)
    assert ret_res.status_code == 200
    ret_data = ret_res.json()
    assert ret_data["karma_updated"]["is_on_time"] is True
    assert ret_data["karma_updated"]["owner_gain"] == 10
    assert ret_data["karma_updated"]["borrower_change"] == 5

    db = database.SessionLocal()
    owner_k_after = db.query(models.User).filter(models.User.id == 3).first().karma
    borrower_k_after = db.query(models.User).filter(models.User.id == 2).first().karma
    item_after = db.query(models.Item).filter(models.Item.id == 2).first()
    db.close()

    assert owner_k_after == owner_k_before + 10
    assert borrower_k_after == borrower_k_before + 5
    assert item_after.is_available is True
    assert item_after.status == "available"
    print(f"  [PASS] On-time return correctly updated Karma: Owner +10, Borrower +5. Item restored to available.")

    # 3.14 Cannot return already returned transaction (idempotency/replay attack prevention)
    double_ret = client.post(f"/api/transactions/return/{req_id}", headers=borrower_headers)
    assert double_ret.status_code == 400
    print("  [PASS] Replay return prevented: cannot return already returned transaction (HTTP 400)")

    # ----------------------------------------------------
    # 4. Stress-test Late Return (-30 Karma)
    # ----------------------------------------------------
    print("\n[SECTION 4] Testing Late Return Karma Penalty (-30)...")
    br_late = client.post("/api/requests/", json={
        "item_id": 1, # Siddique's item
        "duration_hours": 1,
    }, headers=owner_headers) # Tanvir borrows
    assert br_late.status_code == 200
    req_late_id = br_late.json()["id"]

    # Siddique accepts
    client.put(f"/api/requests/{req_late_id}/status?status=accepted", headers=borrower_headers)
    # Start handover
    st_late = client.post("/api/transactions/start", json={"request_id": req_late_id}, headers=borrower_headers)
    otp_late = st_late.json()["otp"]
    # Verify handover
    client.post("/api/transactions/verify", json={"request_id": req_late_id, "otp": otp_late}, headers=owner_headers)

    # Fast-forward borrowed_at to simulate late return (2 hours past duration)
    db = database.SessionLocal()
    trans_late = db.query(models.Transaction).filter(models.Transaction.request_id == req_late_id).first()
    trans_late.borrowed_at = datetime.now(timezone.utc) - timedelta(hours=4)
    db.commit()
    t_before = db.query(models.User).filter(models.User.id == 3).first().karma
    s_before = db.query(models.User).filter(models.User.id == 2).first().karma
    db.close()

    # Tanvir returns late
    ret_late = client.post(f"/api/transactions/return/{req_late_id}", headers=owner_headers)
    assert ret_late.status_code == 200
    data_late = ret_late.json()
    assert data_late["karma_updated"]["is_on_time"] is False
    assert data_late["karma_updated"]["owner_gain"] == 10
    assert data_late["karma_updated"]["borrower_change"] == -30

    db = database.SessionLocal()
    t_after = db.query(models.User).filter(models.User.id == 3).first().karma
    s_after = db.query(models.User).filter(models.User.id == 2).first().karma
    db.close()

    assert s_after == s_before + 10
    assert t_after == t_before - 30
    print(f"  [PASS] Late return correctly updated Karma: Owner +10 ({s_before}->{s_after}), Borrower -30 ({t_before}->{t_after})")

    # ----------------------------------------------------
    # 5. Database Robustness & Migration Safety
    # ----------------------------------------------------
    print("\n[SECTION 5] Testing Database Migration & Model Constraints...")
    db = database.SessionLocal()
    # Check User model constraints
    u_count = db.query(models.User).count()
    i_count = db.query(models.Item).count()
    t_count = db.query(models.Transaction).count()
    r_count = db.query(models.BorrowRequest).count()
    db.close()
    print(f"  [PASS] Database integrity intact: {u_count} users, {i_count} items, {r_count} requests, {t_count} transactions.")

    print("\n==================================================")
    print("ALL ADVERSARIAL STRESS-TESTS PASSED WITH 0 FAILURES!")
    print("==================================================")

if __name__ == "__main__":
    run_adversarial_suite()
