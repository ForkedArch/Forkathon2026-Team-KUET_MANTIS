import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app import models, database
from test_m1 import ASGIClient

client = ASGIClient(app)

def run_adversarial_tests():
    print("=" * 60)
    print("STARTING ADVERSARIAL STRESS TEST SUITE: KUET KARMA & TRANSACTION STATES")
    print("=" * 60)

    # Setup test users and tokens
    owner_email = "adv_owner2507001@stud.kuet.ac.bd"
    borrower_email = "adv_borrower2507002@stud.kuet.ac.bd"
    unauth_email = "adv_unauth2507003@stud.kuet.ac.bd"

    for email, name in [(owner_email, "Adv Owner"), (borrower_email, "Adv Borrower"), (unauth_email, "Adv Stranger")]:
        reg = client.post("/api/auth/register", json={
            "name": name,
            "email": email,
            "password": "advpassword123"
        })
        if reg.status_code != 200 and "Email already registered" not in reg.text:
            raise RuntimeError(f"Failed to register {email}: {reg.text}")

    tok_owner = client.post("/api/auth/login", json={"email": owner_email, "password": "advpassword123"}).json()["access_token"]
    tok_borrower = client.post("/api/auth/login", json={"email": borrower_email, "password": "advpassword123"}).json()["access_token"]
    tok_unauth = client.post("/api/auth/login", json={"email": unauth_email, "password": "advpassword123"}).json()["access_token"]

    h_owner = {"Authorization": f"Bearer {tok_owner}"}
    h_borrower = {"Authorization": f"Bearer {tok_borrower}"}
    h_unauth = {"Authorization": f"Bearer {tok_unauth}"}

    results = {
        "boundary_timing": [],
        "karma_scoring": [],
        "negative_karma": [],
        "double_returns": [],
        "unauthorized_returns": [],
        "state_vulnerabilities": []
    }

    # Helper function to create, accept, and start a handover
    def setup_active_transaction(duration_hours=2):
        item_res = client.post("/api/items/", json={
            "title": f"Timing Test Item {os.urandom(4).hex()}",
            "type": "lend",
            "category": "Electronics"
        }, headers=h_owner)
        assert item_res.status_code == 201, item_res.text
        item_id = item_res.json()["id"]

        req_res = client.post("/api/requests/", json={
            "item_id": item_id,
            "duration_hours": duration_hours
        }, headers=h_borrower)
        assert req_res.status_code == 200, req_res.text
        req_id = req_res.json()["id"]

        client.put(f"/api/requests/{req_id}/status?status=accepted", headers=h_owner)
        start_res = client.post("/api/transactions/start", json={"request_id": req_id}, headers=h_owner)
        assert start_res.status_code == 200
        otp = start_res.json()["otp"]

        ver_res = client.post("/api/transactions/verify", json={"request_id": req_id, "otp": otp}, headers=h_borrower)
        assert ver_res.status_code == 200

        return req_id, item_id

    # =========================================================================
    # SECTION 1: EXACT BOUNDARY TIMING ON RETURNS
    # =========================================================================
    print("\n" + "-" * 50)
    print("SUITE 1: Exact Boundary Timing on Returns")
    print("-" * 50)

    # 1.1 Mathematical Exact Boundary (now == due_time)
    # Using fixed mock datetime to eliminate in-flight network/CPU latency
    fixed_borrowed = datetime(2026, 9, 10, 12, 0, 0, tzinfo=timezone.utc)
    exact_due = fixed_borrowed + timedelta(hours=2) # 14:00:00

    req_id, item_id = setup_active_transaction(duration_hours=2)
    db = database.SessionLocal()
    trans = db.query(models.Transaction).filter(models.Transaction.request_id == req_id).first()
    trans.borrowed_at = fixed_borrowed
    db.commit()
    db.close()

    # Return exactly at due time: now == exact_due
    with patch("app.routes.transactions.datetime") as mock_dt:
        mock_dt.now.return_value = exact_due
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
        ret_exact = client.post(f"/api/transactions/return/{req_id}", headers=h_borrower)

    assert ret_exact.status_code == 200, ret_exact.text
    is_on_time_exact = ret_exact.json()["karma_updated"]["is_on_time"]
    assert is_on_time_exact is True, f"Expected exact boundary (now == due_time) to be on-time, got {is_on_time_exact}"
    assert ret_exact.json()["karma_updated"]["borrower_change"] == 5
    assert ret_exact.json()["karma_updated"]["owner_gain"] == 10
    print(f"  [1.1] Exact Boundary Return (now == due_time) -> PASS: is_on_time={is_on_time_exact}, borrower_change=+5, owner_gain=+10")
    results["boundary_timing"].append(("exact_boundary", True))

    # 1.2 1 Second Before Due Time (13:59:59)
    req_id, item_id = setup_active_transaction(duration_hours=2)
    db = database.SessionLocal()
    trans = db.query(models.Transaction).filter(models.Transaction.request_id == req_id).first()
    trans.borrowed_at = fixed_borrowed
    db.commit()
    db.close()

    time_1s_before = exact_due - timedelta(seconds=1)
    with patch("app.routes.transactions.datetime") as mock_dt:
        mock_dt.now.return_value = time_1s_before
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
        ret_1s_before = client.post(f"/api/transactions/return/{req_id}", headers=h_borrower)

    assert ret_1s_before.status_code == 200
    is_on_time_1s_before = ret_1s_before.json()["karma_updated"]["is_on_time"]
    assert is_on_time_1s_before is True, "Expected 1s before due time to be on-time!"
    assert ret_1s_before.json()["karma_updated"]["borrower_change"] == 5
    print(f"  [1.2] 1s Before Due Time (due - 1s) -> PASS: is_on_time={is_on_time_1s_before}, borrower_change=+5")
    results["boundary_timing"].append(("1s_before", True))

    # 1.3 1 Second After Due Time (14:00:01)
    req_id, item_id = setup_active_transaction(duration_hours=2)
    db = database.SessionLocal()
    trans = db.query(models.Transaction).filter(models.Transaction.request_id == req_id).first()
    trans.borrowed_at = fixed_borrowed
    db.commit()
    db.close()

    time_1s_after = exact_due + timedelta(seconds=1)
    with patch("app.routes.transactions.datetime") as mock_dt:
        mock_dt.now.return_value = time_1s_after
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
        ret_1s_after = client.post(f"/api/transactions/return/{req_id}", headers=h_borrower)

    assert ret_1s_after.status_code == 200
    is_on_time_1s_after = ret_1s_after.json()["karma_updated"]["is_on_time"]
    assert is_on_time_1s_after is False, "Expected 1s after due time to be late!"
    assert ret_1s_after.json()["karma_updated"]["borrower_change"] == -30
    assert ret_1s_after.json()["karma_updated"]["owner_gain"] == 10
    print(f"  [1.3] 1s After Due Time (due + 1s) -> PASS: is_on_time={is_on_time_1s_after}, borrower_change=-30, owner_gain=+10")
    results["boundary_timing"].append(("1s_after", False))

    # 1.4 Days After Due Time (7 days late)
    req_id, item_id = setup_active_transaction(duration_hours=2)
    db = database.SessionLocal()
    trans = db.query(models.Transaction).filter(models.Transaction.request_id == req_id).first()
    trans.borrowed_at = fixed_borrowed
    db.commit()
    db.close()

    time_7d_after = exact_due + timedelta(days=7)
    with patch("app.routes.transactions.datetime") as mock_dt:
        mock_dt.now.return_value = time_7d_after
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
        ret_days_after = client.post(f"/api/transactions/return/{req_id}", headers=h_borrower)

    assert ret_days_after.status_code == 200
    is_on_time_days = ret_days_after.json()["karma_updated"]["is_on_time"]
    assert is_on_time_days is False, "Expected 7 days after due time to be late!"
    assert ret_days_after.json()["karma_updated"]["borrower_change"] == -30
    assert ret_days_after.json()["karma_updated"]["owner_gain"] == 10
    print(f"  [1.4] 7 Days After Due Time (due + 7d) -> PASS: is_on_time={is_on_time_days}, borrower_change=-30, owner_gain=+10")
    results["boundary_timing"].append(("days_after", False))

    # =========================================================================
    # SECTION 2: KARMA SCORING CORRECTNESS & NEGATIVE SCORES
    # =========================================================================
    print("\n" + "-" * 50)
    print("SUITE 2: Successive Transactions & Negative Karma Scoring")
    print("-" * 50)

    # Reset user karma to 100 for clean mathematical verification
    db = database.SessionLocal()
    u_o = db.query(models.User).filter(models.User.email == owner_email).first()
    u_b = db.query(models.User).filter(models.User.email == borrower_email).first()
    u_o.karma = 100
    u_o.trust_score = 100.0
    u_b.karma = 100
    u_b.trust_score = 100.0
    db.commit()
    db.close()

    # 2.1 Three successive on-time returns: owner should get +10, +10, +10 (100 -> 130)
    # borrower should get +5, +5, +5 (100 -> 115)
    for i in range(1, 4):
        rid, _ = setup_active_transaction(duration_hours=5)
        r = client.post(f"/api/transactions/return/{rid}", headers=h_borrower)
        assert r.status_code == 200
        assert r.json()["karma_updated"]["is_on_time"] is True

    db = database.SessionLocal()
    u_o = db.query(models.User).filter(models.User.email == owner_email).first()
    u_b = db.query(models.User).filter(models.User.email == borrower_email).first()
    assert u_o.karma == 130, f"Expected owner karma 130, got {u_o.karma}"
    assert u_b.karma == 115, f"Expected borrower karma 115, got {u_b.karma}"
    assert u_o.trust_score == 130.0
    assert u_b.trust_score == 115.0
    db.close()
    print(f"  [2.1] 3 Successive On-Time -> PASS: Owner karma = 130, Borrower karma = 115")
    results["karma_scoring"].append(("successive_on_time", True))

    # 2.2 Drive borrower karma into negative territory via successive late returns
    # Current borrower karma = 115.
    # Late 1: 115 - 30 = 85
    # Late 2: 85 - 30 = 55
    # Late 3: 55 - 30 = 25
    # Late 4: 25 - 30 = -5  <-- Enters negative karma!
    # Late 5: -5 - 30 = -35 <-- Deep negative karma!
    expected_borrower_scores = [85, 55, 25, -5, -35]
    for idx, expected_score in enumerate(expected_borrower_scores, 1):
        rid, _ = setup_active_transaction(duration_hours=1)
        # Force late by setting borrowed_at to 10 hours ago
        db = database.SessionLocal()
        trans = db.query(models.Transaction).filter(models.Transaction.request_id == rid).first()
        trans.borrowed_at = datetime.now(timezone.utc) - timedelta(hours=10)
        db.commit()
        db.close()

        r = client.post(f"/api/transactions/return/{rid}", headers=h_borrower)
        assert r.status_code == 200
        assert r.json()["karma_updated"]["is_on_time"] is False
        assert r.json()["karma_updated"]["borrower_change"] == -30

        db = database.SessionLocal()
        u_b = db.query(models.User).filter(models.User.email == borrower_email).first()
        actual_karma = u_b.karma
        actual_trust = u_b.trust_score
        db.close()
        assert actual_karma == expected_score, f"Expected {expected_score}, got {actual_karma}"
        assert actual_trust == float(expected_score)
        print(f"  [2.2.{idx}] Late Return {idx} -> PASS: Borrower karma {actual_karma} (trust_score {actual_trust})")

    # 2.3 Verify profile & item serialization with negative karma
    prof = client.get("/api/auth/current", headers=h_borrower)
    assert prof.status_code == 200
    assert prof.json()["user"]["karma"] == -35
    assert prof.json()["user"]["trust_score"] == -35.0

    item_neg = client.post("/api/items/", json={
        "title": "Item by Negative Karma User",
        "type": "lend",
        "category": "Books"
    }, headers=h_borrower)
    assert item_neg.status_code == 201
    item_neg_data = item_neg.json()
    assert item_neg_data["karma"] == -35
    assert item_neg_data["trust_rating"] == -35.0
    print("  [2.3] Negative Karma Serialization -> PASS: UserOut and ItemOut serialize negative karma correctly (-35)")
    results["negative_karma"].append(("negative_serialization", True))

    # 2.4 Recovery from negative karma: on-time return adds +5 (-35 -> -30)
    rid, _ = setup_active_transaction(duration_hours=2)
    r = client.post(f"/api/transactions/return/{rid}", headers=h_borrower)
    assert r.status_code == 200
    db = database.SessionLocal()
    u_b = db.query(models.User).filter(models.User.email == borrower_email).first()
    assert u_b.karma == -30, f"Expected -30, got {u_b.karma}"
    db.close()
    print("  [2.4] Recovery from Negative Karma -> PASS: -35 + 5 = -30")
    results["negative_karma"].append(("negative_recovery", True))

    # =========================================================================
    # SECTION 3: DOUBLE-RETURNS & UNAUTHORIZED RETURNS
    # =========================================================================
    print("\n" + "-" * 50)
    print("SUITE 3: Double-Returns & Unauthorized Returns")
    print("-" * 50)

    # 3.1 Immediate double-return
    rid, _ = setup_active_transaction(duration_hours=2)
    r_first = client.post(f"/api/transactions/return/{rid}", headers=h_borrower)
    assert r_first.status_code == 200, r_first.text

    # Second return call without re-verifying
    r_second = client.post(f"/api/transactions/return/{rid}", headers=h_borrower)
    assert r_second.status_code == 400, f"Expected 400, got {r_second.status_code}: {r_second.text}"
    assert "Item not currently borrowed" in r_second.text
    print("  [3.1] Immediate Double-Return -> PASS: Rejected with HTTP 400 'Item not currently borrowed'")
    results["double_returns"].append(("immediate_double_return", True))

    # 3.2 Unauthorized returns
    rid, _ = setup_active_transaction(duration_hours=2)

    # 3.2.1 Unauthenticated user
    r_no_auth = client.post(f"/api/transactions/return/{rid}")
    assert r_no_auth.status_code in [401, 403], f"Expected 401 or 403, got {r_no_auth.status_code}"
    print(f"  [3.2.1] Unauthenticated Return -> PASS: Rejected with HTTP {r_no_auth.status_code}")
    results["unauthorized_returns"].append(("unauthenticated", True))

    # 3.2.2 Owner attempts to call return
    r_owner_ret = client.post(f"/api/transactions/return/{rid}", headers=h_owner)
    assert r_owner_ret.status_code == 403, f"Expected 403, got {r_owner_ret.status_code}"
    assert "Only borrower can request return" in r_owner_ret.text
    print("  [3.2.2] Owner Attempting Return -> PASS: Rejected with HTTP 403 'Only borrower can request return'")
    results["unauthorized_returns"].append(("owner_return", True))

    # 3.2.3 Unrelated third-party student attempts to call return
    r_stranger_ret = client.post(f"/api/transactions/return/{rid}", headers=h_unauth)
    assert r_stranger_ret.status_code == 403, f"Expected 403, got {r_stranger_ret.status_code}"
    assert "Only borrower can request return" in r_stranger_ret.text
    print("  [3.2.3] Stranger Attempting Return -> PASS: Rejected with HTTP 403 'Only borrower can request return'")
    results["unauthorized_returns"].append(("stranger_return", True))

    # 3.2.4 Non-existent request ID
    r_not_found = client.post("/api/transactions/return/999999", headers=h_borrower)
    assert r_not_found.status_code == 404, f"Expected 404, got {r_not_found.status_code}"
    print("  [3.2.4] Non-Existent Request Return -> PASS: Rejected with HTTP 404")
    results["unauthorized_returns"].append(("not_found", True))

    # 3.2.5 Return before handover verification (status is pending)
    item_res = client.post("/api/items/", json={
        "title": "Unverified Handover Item",
        "type": "lend",
        "category": "Tools"
    }, headers=h_owner)
    item_id = item_res.json()["id"]
    req_res = client.post("/api/requests/", json={"item_id": item_id, "duration_hours": 2}, headers=h_borrower)
    req_id = req_res.json()["id"]
    client.put(f"/api/requests/{req_id}/status?status=accepted", headers=h_owner)
    client.post("/api/transactions/start", json={"request_id": req_id}, headers=h_owner)

    r_premature = client.post(f"/api/transactions/return/{req_id}", headers=h_borrower)
    assert r_premature.status_code == 400, f"Expected 400, got {r_premature.status_code}"
    assert "Item not currently borrowed" in r_premature.text
    print("  [3.2.5] Premature Return Before Handover -> PASS: Rejected with HTTP 400 'Item not currently borrowed'")
    results["unauthorized_returns"].append(("premature_return", True))

    # =========================================================================
    # SECTION 4: STATE MACHINE VULNERABILITIES (ADVERSARIAL STRESS TEST)
    # =========================================================================
    print("\n" + "-" * 50)
    print("SUITE 4: State Machine Stress Testing & Vulnerability Discovery")
    print("-" * 50)

    # 4.1 Replay attack & Infinite Karma Mining Loop
    item_vuln = client.post("/api/items/", json={"title": "Vulnerability Probe 1", "type": "lend", "category": "General"}, headers=h_owner).json()
    req_vuln = client.post("/api/requests/", json={"item_id": item_vuln["id"], "duration_hours": 1}, headers=h_borrower).json()
    rv_id = req_vuln["id"]
    client.put(f"/api/requests/{rv_id}/status?status=accepted", headers=h_owner)
    st = client.post("/api/transactions/start", json={"request_id": rv_id}, headers=h_owner).json()
    otp_used = st["otp"]
    client.post("/api/transactions/verify", json={"request_id": rv_id, "otp": otp_used}, headers=h_borrower)

    # Initial return
    r_ret1 = client.post(f"/api/transactions/return/{rv_id}", headers=h_borrower)
    assert r_ret1.status_code == 200

    # Probe: can borrower re-verify with the same OTP?
    r_reverify = client.post("/api/transactions/verify", json={"request_id": rv_id, "otp": otp_used}, headers=h_borrower)
    vuln_reverify = (r_reverify.status_code == 200)
    print(f"  [4.1] Probe: Re-verify after return accepted? -> Status: {r_reverify.status_code} (VULNERABLE={vuln_reverify})")

    if vuln_reverify:
        # Check if return can be called again for free karma
        r_ret_replay = client.post(f"/api/transactions/return/{rv_id}", headers=h_borrower)
        vuln_karma_mining = (r_ret_replay.status_code == 200)
        print(f"  [4.1] Probe: Second return after re-verify accepted? -> Status: {r_ret_replay.status_code} (EXPLOIT CONFIRMED={vuln_karma_mining})")
        results["state_vulnerabilities"].append({
            "name": "Infinite Karma Mining via Handover Re-verification Replay",
            "severity": "CRITICAL",
            "confirmed": vuln_karma_mining,
            "detail": "Borrower can reuse the uninvalidated OTP to re-verify an already returned transaction, resetting status to 'borrowed' and repeatedly collecting +5 borrower / +10 owner karma."
        })

    # 4.2 Late return penalty evasion
    item_vuln2 = client.post("/api/items/", json={"title": "Vulnerability Probe 2", "type": "lend", "category": "General"}, headers=h_owner).json()
    req_vuln2 = client.post("/api/requests/", json={"item_id": item_vuln2["id"], "duration_hours": 1}, headers=h_borrower).json()
    rv2_id = req_vuln2["id"]
    client.put(f"/api/requests/{rv2_id}/status?status=accepted", headers=h_owner)
    st2 = client.post("/api/transactions/start", json={"request_id": rv2_id}, headers=h_owner).json()
    otp2 = st2["otp"]
    client.post("/api/transactions/verify", json={"request_id": rv2_id, "otp": otp2}, headers=h_borrower)

    # Simulate 24 hours overdue
    db = database.SessionLocal()
    t = db.query(models.Transaction).filter(models.Transaction.request_id == rv2_id).first()
    t.borrowed_at = datetime.now(timezone.utc) - timedelta(hours=24)
    db.commit()
    db.close()

    # Re-verify while borrowed to reset borrowed_at to now
    r_reset_clock = client.post("/api/transactions/verify", json={"request_id": rv2_id, "otp": otp2}, headers=h_borrower)
    vuln_reset = (r_reset_clock.status_code == 200)
    r_evaded_return = client.post(f"/api/transactions/return/{rv2_id}", headers=h_borrower)
    evaded_is_on_time = r_evaded_return.json().get("karma_updated", {}).get("is_on_time", False)
    print(f"  [4.2] Probe: Late penalty evaded via re-verify? -> (VULNERABLE={evaded_is_on_time})")
    results["state_vulnerabilities"].append({
        "name": "Late Penalty Evasion via Mid-Borrow Re-verification",
        "severity": "HIGH",
        "confirmed": (evaded_is_on_time is True),
        "detail": "Calling /api/transactions/verify while already borrowed resets borrowed_at to the current timestamp, converting an overdue return into an on-time return (+5 instead of -30)."
    })

    # 4.3 Owner mid-borrow restart lockout
    item_vuln3 = client.post("/api/items/", json={"title": "Vulnerability Probe 3", "type": "lend", "category": "General"}, headers=h_owner).json()
    req_vuln3 = client.post("/api/requests/", json={"item_id": item_vuln3["id"], "duration_hours": 1}, headers=h_borrower).json()
    rv3_id = req_vuln3["id"]
    client.put(f"/api/requests/{rv3_id}/status?status=accepted", headers=h_owner)
    st3 = client.post("/api/transactions/start", json={"request_id": rv3_id}, headers=h_owner).json()
    otp3 = st3["otp"]
    client.post("/api/transactions/verify", json={"request_id": rv3_id, "otp": otp3}, headers=h_borrower)

    # Owner calls start again mid-borrow
    r_owner_restart = client.post("/api/transactions/start", json={"request_id": rv3_id}, headers=h_owner)
    r_locked_return = client.post(f"/api/transactions/return/{rv3_id}", headers=h_borrower)
    vuln_lockout = (r_owner_restart.status_code == 200 and r_locked_return.status_code == 400)
    print(f"  [4.3] Probe: Owner restarted mid-borrow & locked borrower out of returning? -> (VULNERABLE={vuln_lockout})")
    results["state_vulnerabilities"].append({
        "name": "Owner Mid-Borrow Transaction Reset & Return Lockout",
        "severity": "HIGH",
        "confirmed": vuln_lockout,
        "detail": "Owner can call /api/transactions/start while item is actively borrowed, resetting status to 'pending' and generating a new OTP, preventing the borrower from returning the item."
    })

    # 4.4 Negative duration acceptance
    item_vuln4 = client.post("/api/items/", json={"title": "Vulnerability Probe 4", "type": "lend", "category": "General"}, headers=h_owner).json()
    r_neg_dur = client.post("/api/requests/", json={"item_id": item_vuln4["id"], "duration_hours": -5}, headers=h_borrower)
    vuln_neg_dur = (r_neg_dur.status_code == 200)
    print(f"  [4.4] Probe: Negative duration (-5 hours) accepted? -> Status: {r_neg_dur.status_code} (VULNERABLE={vuln_neg_dur})")
    results["state_vulnerabilities"].append({
        "name": "Unvalidated Negative Duration in Borrow Requests",
        "severity": "MEDIUM",
        "confirmed": vuln_neg_dur,
        "detail": "BorrowRequestCreate lacks gt=0 validation, allowing negative duration_hours which guarantees an instant -30 penalty upon return."
    })

    print("\n" + "=" * 60)
    print("ADVERSARIAL STRESS TEST SUITE COMPLETED")
    print("=" * 60)

    print("\nSUMMARY OF DISCOVERED VULNERABILITIES:")
    for v in results["state_vulnerabilities"]:
        print(f"- [{v['severity']}] {v['name']} (Confirmed: {v['confirmed']})")
        print(f"    Detail: {v['detail']}")

    return results

if __name__ == "__main__":
    run_adversarial_tests()
