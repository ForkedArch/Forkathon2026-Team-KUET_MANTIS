import os
import sys
import json
import random
import asyncio
import concurrent.futures
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app import models, database
from test_m1 import ASGIClient, ASGIResponse

class RobustASGIClient(ASGIClient):
    async def _request_async(self, method, path, headers=None, json_payload=None, data=None, params=None):
        try:
            return await super()._request_async(method, path, headers=headers, json_payload=json_payload, data=data, params=params)
        except Exception as exc:
            return ASGIResponse(500, [(b"content-type", b"application/json")], f'{{"error": "{type(exc).__name__}", "detail": "{str(exc)}"}}'.encode("utf-8"))

client = RobustASGIClient(app)

results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "findings": []
}

def record_finding(category, title, attack_input, status_code, expected_status, details, is_bug=False):
    results["total"] += 1
    if not is_bug:
        results["passed"] += 1
    else:
        results["failed"] += 1
    entry = {
        "category": category,
        "title": title,
        "attack_input": attack_input,
        "status_code": status_code,
        "expected_status": expected_status,
        "details": details,
        "is_bug": is_bug
    }
    results["findings"].append(entry)
    status_tag = "FAIL (BUG)" if is_bug else "PASS (HANDLED)"
    print(f"[{status_tag}] {category} -> {title} | HTTP {status_code} (Expected {expected_status})")
    if is_bug:
        print(f"       Details: {details}")


# =========================================================================
# SUITE 1: EMAIL VALIDATION & SPOOFING ATTACKS
# =========================================================================
def test_suite_emails():
    print("\n" + "=" * 60)
    print("SUITE 1: EMAIL VALIDATION & REGEX ATTACKS")
    print("=" * 60)

    # 1.1 Evil domain suffixes
    evil_domain_cases = [
        ("Suffix append (.evil.com)", "user2507028@stud.kuet.ac.bd.evil.com", 400),
        ("Subdomain prefix (sub.stud)", "user2507028@sub.stud.kuet.ac.bd", 400),
        ("Fake stud domain (fake-stud)", "user2507028@fake-stud.kuet.ac.bd", 400),
        ("Official faculty domain (@kuet.ac.bd)", "user2507028@kuet.ac.bd", 400),
        ("Generic domain (@gmail.com)", "user2507028@gmail.com", 400),
        ("Similar domain (@stud_kuet.ac.bd)", "user2507028@stud_kuet.ac.bd", 400),
        ("Similar TLD (@stud.kuet.edu.bd)", "user2507028@stud.kuet.edu.bd", 400),
        ("Dot typo (@studkuet.ac.bd)", "user2507028@studkuet.ac.bd", 400),
        ("Trailing dot domain (@stud.kuet.ac.bd.)", "user2507028@stud.kuet.ac.bd.", 400),
    ]

    for label, email, exp in evil_domain_cases:
        res = client.post("/api/auth/register", json={
            "name": f"Test {label}",
            "email": email,
            "password": "Password123!"
        })
        is_bug = res.status_code not in (400, 422)
        record_finding(
            category="Email Domain Attacks",
            title=label,
            attack_input=email,
            status_code=res.status_code,
            expected_status="400 or 422",
            details=res.text[:150],
            is_bug=is_bug
        )

    # 1.2 Bad local parts & missing numbers
    bad_local_cases = [
        ("No digits at all", "tanvir@stud.kuet.ac.bd", 400),
        ("Only 1 digit", "tanvir1@stud.kuet.ac.bd", 400),
        ("Only 2 digits (batch only)", "tanvir25@stud.kuet.ac.bd", 400),
        ("Only 4 digits (batch+dept)", "tanvir2507@stud.kuet.ac.bd", 400),
        ("Only 6 digits (missing roll digit)", "tanvir250701@stud.kuet.ac.bd", 400),
        ("7 digits with trailing letters", "tanvir2507028xyz@stud.kuet.ac.bd", 400),
        ("Empty local part", "@stud.kuet.ac.bd", 422),
        ("Whitespace in local part", "tanvir 2507028@stud.kuet.ac.bd", 422),
        ("Multiple @ symbols", "tanvir2507028@evil@stud.kuet.ac.bd", 422),
    ]

    for label, email, exp in bad_local_cases:
        res = client.post("/api/auth/register", json={
            "name": f"Test {label}",
            "email": email,
            "password": "Password123!"
        })
        is_bug = res.status_code not in (400, 422)
        record_finding(
            category="Bad Local Parts",
            title=label,
            attack_input=email,
            status_code=res.status_code,
            expected_status="400 or 422",
            details=res.text[:150],
            is_bug=is_bug
        )


# =========================================================================
# SUITE 2: UNICODE & BOUNDARY ROLL TESTING
# =========================================================================
def test_suite_unicode_and_boundaries():
    print("\n" + "=" * 60)
    print("SUITE 2: UNICODE & BOUNDARY ROLLS")
    print("=" * 60)

    # 2.1 Boundary Rolls with fresh batches
    fresh_batch = str(random.randint(60, 89))
    boundary_cases = [
        ("Minimum boundary: batch 00, dept 00, roll 000", f"min_{os.urandom(2).hex()}0000000@stud.kuet.ac.bd", "00", "00", "000"),
        ("Maximum boundary: batch 99, dept 99, roll 999", f"max_{os.urandom(2).hex()}9999999@stud.kuet.ac.bd", "99", "99", "999"),
        ("Zero leading roll: roll 001", f"zero01_{fresh_batch}07001@stud.kuet.ac.bd", fresh_batch, "07", "001"),
        ("Zero leading roll: roll 010", f"zero10_{fresh_batch}07010@stud.kuet.ac.bd", fresh_batch, "07", "010"),
    ]

    for label, email, exp_b, exp_d, exp_r in boundary_cases:
        res = client.post("/api/auth/register", json={
            "name": f"Student {exp_r}",
            "email": email,
            "password": "Password123!"
        })
        if res.status_code == 400 and "already registered" in res.text:
            db = database.SessionLocal()
            u = db.query(models.User).filter(models.User.batch == exp_b, models.User.dept == exp_d, models.User.roll == exp_r).first()
            db.close()
            is_bug = not (u and u.batch == exp_b and u.dept == exp_d and u.roll == exp_r)
            record_finding(
                category="Boundary Rolls",
                title=f"{label} (Existing)",
                attack_input=email,
                status_code=res.status_code,
                expected_status="200 (stored correctly)",
                details=f"DB values: batch={u.batch}, dept={u.dept}, roll={u.roll}" if u else "User not found",
                is_bug=is_bug
            )
        else:
            is_bug = res.status_code != 200
            if not is_bug:
                u_data = res.json()
                if u_data["batch"] != exp_b or u_data["dept"] != exp_d or u_data["roll"] != exp_r:
                    is_bug = True
                    details = f"Decoded batch={u_data['batch']}, dept={u_data['dept']}, roll={u_data['roll']} vs expected {exp_b},{exp_d},{exp_r}"
                else:
                    details = f"Correctly decoded strings: {exp_b}-{exp_d}-{exp_r}"
            else:
                details = res.text[:150]
            record_finding(
                category="Boundary Rolls",
                title=label,
                attack_input=email,
                status_code=res.status_code,
                expected_status="200",
                details=details,
                is_bug=is_bug
            )

    # 2.2 Unicode in Name and Credentials
    fresh_roll = random.randint(100, 400)
    unicode_cases = [
        ("Bangla Bengali script in Name", "মুহাম্মদ তানভীর আহমেদ", f"bangla_name{fresh_batch}07{fresh_roll}@stud.kuet.ac.bd"),
        ("Arabic script in Name", "محمد عبد الله", f"arabic_name{fresh_batch}07{fresh_roll+1}@stud.kuet.ac.bd"),
        ("CJK Chinese script in Name", "王伟", f"chinese_name{fresh_batch}07{fresh_roll+2}@stud.kuet.ac.bd"),
        ("Emoji in Name", "Student 🎓🔥 Kuet", f"emoji_name{fresh_batch}07{fresh_roll+3}@stud.kuet.ac.bd"),
        ("RTL direction override in Name", "\u202Ereversed_name\u202C", f"rtl_name{fresh_batch}07{fresh_roll+4}@stud.kuet.ac.bd"),
        ("Zero-width space in Name", "John\u200BDoe", f"zwsp_name{fresh_batch}07{fresh_roll+5}@stud.kuet.ac.bd"),
    ]

    for label, name, email in unicode_cases:
        res = client.post("/api/auth/register", json={
            "name": name,
            "email": email,
            "password": "Password123!_unicode"
        })
        is_bug = res.status_code not in (200, 400)
        record_finding(
            category="Unicode Handling",
            title=label,
            attack_input=name,
            status_code=res.status_code,
            expected_status="200 (No 500)",
            details=res.text[:150],
            is_bug=is_bug
        )

    # 2.3 Unicode Homoglyph / Non-ASCII Digits in Roll Number
    bengali_email = f"tanvir২৫০৭{random.randint(100,999)}@stud.kuet.ac.bd"
    res_bengali = client.post("/api/auth/register", json={
        "name": "Bengali Student",
        "email": bengali_email,
        "password": "Password123!"
    })
    # If accepted, it allows non-ASCII digit spoofing of student roll
    bengali_accepted = (res_bengali.status_code == 200)
    record_finding(
        category="Unicode Roll Spoofing",
        title="Bengali digits in student email ID (২৫০৭...)",
        attack_input=bengali_email,
        status_code=res_bengali.status_code,
        expected_status="400 (Only ASCII digits 0-9 allowed)",
        details=f"Decoded: batch={res_bengali.json().get('batch')}, roll={res_bengali.json().get('roll')}" if bengali_accepted else res_bengali.text[:120],
        is_bug=bengali_accepted
    )


# =========================================================================
# SUITE 3: SQL INJECTION & PAYLOAD ATTACKS
# =========================================================================
def test_suite_sqli():
    print("\n" + "=" * 60)
    print("SUITE 3: SQL INJECTION ATTACKS (AUTH & ITEMS)")
    print("=" * 60)

    # 3.1 SQLi in Auth Register
    sqli_auth_cases = [
        ("SQLi tautology in name", "' OR '1'='1", f"sqli_name{random.randint(50,59)}07041@stud.kuet.ac.bd"),
        ("SQLi drop table in name", "Admin'; DROP TABLE users; --", f"sqli_name{random.randint(50,59)}07042@stud.kuet.ac.bd"),
        ("SQLi in password", "' OR 1=1; --", f"sqli_pwd{random.randint(50,59)}07043@stud.kuet.ac.bd"),
        ("SQLi in email local part", "admin'OR'1'='1'2507044@stud.kuet.ac.bd", "admin'OR'1'='1'2507044@stud.kuet.ac.bd"),
    ]

    for label, payload, email in sqli_auth_cases:
        res = client.post("/api/auth/register", json={
            "name": payload,
            "email": email,
            "password": payload
        })
        is_bug = (res.status_code == 500)
        record_finding(
            category="SQL Injection Auth",
            title=label,
            attack_input=payload,
            status_code=res.status_code,
            expected_status="200 or 400/422 (No 500)",
            details=res.text[:150],
            is_bug=is_bug
        )

    # 3.2 SQLi in Items Search & Filtering
    sqli_item_cases = [
        ("Search tautology", "' OR 1=1; --"),
        ("Search drop table", "'; DROP TABLE items; --"),
        ("Search UNION SELECT", "' UNION SELECT 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15; --"),
        ("Search wildcards %", "%%%%%%%%%%"),
        ("Search wildcards _", "__________"),
        ("Search escape characters", "'\\'; --"),
        ("Category SQLi injection", "Lab Equipment' OR '1'='1"),
        ("Type SQLi injection", "lend'; DROP TABLE items; --"),
    ]

    for label, payload in sqli_item_cases:
        if "Category" in label:
            res = client.get(f"/api/items?category={payload}")
        elif "Type" in label:
            res = client.get(f"/api/items?type={payload}")
        else:
            res = client.get(f"/api/items?q={payload}")

        is_bug = (res.status_code == 500)
        record_finding(
            category="SQL Injection Items Query",
            title=label,
            attack_input=payload,
            status_code=res.status_code,
            expected_status="200 (Parameterized query, No 500)",
            details=f"Returned {len(res.json()) if res.status_code == 200 else res.text[:100]} items",
            is_bug=is_bug
        )

    # 3.3 SQLi in Item Creation
    item_sqli_payload = {
        "title": "Oscilloscope'; DROP TABLE items; --",
        "type": "lend",
        "category": "Lab Equipment' UNION SELECT 1--",
        "specs": "' OR 1=1 --",
        "condition": "Good'--",
        "zone": "eee_bldg'--"
    }
    login_res = client.post("/api/auth/login", json={
        "email": "tanvir2207001@stud.kuet.ac.bd",
        "password": "kuet1234"
    })
    token = login_res.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    res_item = client.post("/api/items/", json=item_sqli_payload, headers=h)
    is_bug = (res_item.status_code == 500)
    record_finding(
        category="SQL Injection Item Creation",
        title="Item creation with SQLi strings",
        attack_input=item_sqli_payload["title"],
        status_code=res_item.status_code,
        expected_status="201 (Stored as literal text, No 500)",
        details=res_item.text[:150],
        is_bug=is_bug
    )


# =========================================================================
# SUITE 4: ITEMS API ADVERSARIAL TESTING & EDGE CASES
# =========================================================================
def test_suite_items_adversarial():
    print("\n" + "=" * 60)
    print("SUITE 4: ITEMS API ADVERSARIAL & EDGE CASES")
    print("=" * 60)

    login_res = client.post("/api/auth/login", json={
        "email": "tanvir2207001@stud.kuet.ac.bd",
        "password": "kuet1234"
    })
    token = login_res.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    # 4.1 Missing Title
    res_no_title = client.post("/api/items/", json={"type": "lend", "category": "Books"}, headers=h)
    record_finding(
        category="Items Validation",
        title="Missing title in Item creation",
        attack_input="{'type': 'lend'}",
        status_code=res_no_title.status_code,
        expected_status="422",
        details=res_no_title.text[:150],
        is_bug=res_no_title.status_code != 422
    )

    # 4.2 Blank/Whitespace Title
    res_blank_title = client.post("/api/items/", json={"title": "   ", "type": "lend"}, headers=h)
    record_finding(
        category="Items Validation",
        title="Whitespace title in Item creation",
        attack_input="title='   '",
        status_code=res_blank_title.status_code,
        expected_status="422 or 400",
        details=res_blank_title.text[:150],
        is_bug=(res_blank_title.status_code == 201)
    )

    # 4.3 Arbitrary Item Type
    res_invalid_type = client.post("/api/items/", json={"title": "Invalid Type Test", "type": "destroy"}, headers=h)
    record_finding(
        category="Items Validation",
        title="Invalid item type ('destroy' instead of lend/borrow)",
        attack_input="type='destroy'",
        status_code=res_invalid_type.status_code,
        expected_status="422 or 400",
        details=res_invalid_type.text[:150],
        is_bug=(res_invalid_type.status_code == 201 and res_invalid_type.json().get("type") == "destroy")
    )

    # 4.4 Unauthenticated Item Creation / Owner Spoofing
    res_spoof = client.post("/api/items/", json={
        "title": "Anonymous Spoofed Item",
        "type": "lend",
        "roll": "010"
    })
    spoofed = (res_spoof.status_code == 201 and res_spoof.json().get("roll") == "010")
    record_finding(
        category="Item Authentication",
        title="Unauthenticated item creation with roll spoofing",
        attack_input="roll='010' without Authorization header",
        status_code=res_spoof.status_code,
        expected_status="401 Unauthorized",
        details=f"Attributed to: {res_spoof.json().get('lender_name')}" if res_spoof.status_code == 201 else res_spoof.text[:120],
        is_bug=spoofed
    )

    # 4.5 Item Authorization: Update & Delete another user's item
    res_unauth_update = client.put("/api/items/1", json={"title": "Hacked Title", "category": "Calculators"}, headers=h)
    record_finding(
        category="Item Authorization",
        title="Non-owner PUT /api/items/1",
        attack_input="User 1 editing User 2's item",
        status_code=res_unauth_update.status_code,
        expected_status="403",
        details=res_unauth_update.text[:150],
        is_bug=res_unauth_update.status_code != 403
    )

    res_unauth_delete = client.delete("/api/items/1", headers=h)
    record_finding(
        category="Item Authorization",
        title="Non-owner DELETE /api/items/1",
        attack_input="User 1 deleting User 2's item",
        status_code=res_unauth_delete.status_code,
        expected_status="403",
        details=res_unauth_delete.text[:150],
        is_bug=res_unauth_delete.status_code != 403
    )

    # 4.6 Non-existent Item Operations
    res_not_found = client.get("/api/items/999999")
    record_finding(
        category="Item Non-Existent",
        title="GET /api/items/999999",
        attack_input="item_id=999999",
        status_code=res_not_found.status_code,
        expected_status="404",
        details=res_not_found.text[:150],
        is_bug=res_not_found.status_code != 404
    )


# =========================================================================
# SUITE 5: CONCURRENCY & RACE CONDITION STRESS TESTING
# =========================================================================
def test_suite_concurrency():
    print("\n" + "=" * 60)
    print("SUITE 5: CONCURRENT REGISTRATIONS & RACE CONDITIONS")
    print("=" * 60)

    # 5.1 Race condition on exact same email registration
    target_roll = random.randint(500, 999)
    shared_email = f"race_exact_{os.urandom(3).hex()}4507{target_roll}@stud.kuet.ac.bd"
    print(f"  Testing concurrent identical registrations for fresh: {shared_email}")

    def do_register(i):
        return client.post("/api/auth/register", json={
            "name": f"Concurrent User {i}",
            "email": shared_email,
            "password": "Password123!"
        })

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(do_register, i) for i in range(5)]
        responses = [f.result() for f in futures]

    statuses = [r.status_code for r in responses]
    success_count = statuses.count(200)
    client_error_count = statuses.count(400)
    server_error_count = statuses.count(500)

    print(f"  Concurrent exact email responses: {statuses}")
    # BUG: server_error_count > 0 (HTTP 500 unhandled IntegrityError) OR success_count != 1
    is_bug = (server_error_count > 0) or (success_count != 1)
    record_finding(
        category="Concurrency Stress",
        title="5 Concurrent Registrations for Identical Email (Unhandled 500 Crash)",
        attack_input=f"{shared_email} x 5 threads",
        status_code=str(statuses),
        expected_status="One 200, Four 400s (NO 500s)",
        details=f"Successes: {success_count}, 400 errors: {client_error_count}, 500 errors: {server_error_count}. Sample: {[r.text[:60] for r in responses]}",
        is_bug=is_bug
    )

    # 5.2 Race condition on DIFFERENT emails but SAME DECODED (BATCH, DEPT, ROLL)
    diff_roll = random.randint(500, 999)
    email_a = f"alice_{os.urandom(2).hex()}4607{diff_roll}@stud.kuet.ac.bd"
    email_b = f"bob_{os.urandom(2).hex()}4607{diff_roll}@stud.kuet.ac.bd"
    email_c = f"carol_{os.urandom(2).hex()}4607{diff_roll}@stud.kuet.ac.bd"
    test_emails = [email_a, email_b, email_c]
    print(f"  Testing concurrent different emails with same batch/dept/roll (46-07-{diff_roll}): {test_emails}")

    def do_register_diff(email):
        return client.post("/api/auth/register", json={
            "name": f"Diff User {email}",
            "email": email,
            "password": "Password123!"
        })

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(do_register_diff, em) for em in test_emails]
        diff_responses = [f.result() for f in futures]

    diff_statuses = [r.status_code for r in diff_responses]
    diff_success_count = diff_statuses.count(200)
    diff_500_count = diff_statuses.count(500)

    print(f"  Concurrent diff emails same roll responses: {diff_statuses}")
    is_bug_diff = (diff_500_count > 0) or (diff_success_count != 1)
    record_finding(
        category="Concurrency Stress",
        title="3 Concurrent Registrations with Same Roll but Diff Emails (Unhandled 500 Crash)",
        attack_input=f"Same (46, 07, {diff_roll}) x 3 threads",
        status_code=str(diff_statuses),
        expected_status="One 200, Two 400s (NO 500s)",
        details=f"Successes: {diff_success_count}, 500 errors: {diff_500_count}. Sample: {[r.text[:60] for r in diff_responses]}",
        is_bug=is_bug_diff
    )


# =========================================================================
# SUITE 6: SCHEMA VALIDATION & MALFORMED PAYLOAD STRESS
# =========================================================================
def test_suite_schema_validations():
    print("\n" + "=" * 60)
    print("SUITE 6: SCHEMA VALIDATIONS & MALFORMED PAYLOADS")
    print("=" * 60)

    # 6.1 Empty Password & Whitespace Name
    res_empty_pwd = client.post("/api/auth/register", json={
        "name": "Empty Pwd User",
        "email": f"empty_pwd_{os.urandom(2).hex()}4707001@stud.kuet.ac.bd",
        "password": ""
    })
    record_finding(
        category="Schema Validation Auth",
        title="Empty password registration accepted",
        attack_input="password=''",
        status_code=res_empty_pwd.status_code,
        expected_status="422 or 400",
        details=res_empty_pwd.text[:120],
        is_bug=(res_empty_pwd.status_code == 200)
    )

    res_whitespace_name = client.post("/api/auth/register", json={
        "name": "   ",
        "email": f"white_name_{os.urandom(2).hex()}4707002@stud.kuet.ac.bd",
        "password": "Password123!"
    })
    record_finding(
        category="Schema Validation Auth",
        title="Whitespace-only name registration accepted",
        attack_input="name='   '",
        status_code=res_whitespace_name.status_code,
        expected_status="422 or 400",
        details=res_whitespace_name.text[:120],
        is_bug=(res_whitespace_name.status_code == 200)
    )

    # 6.2 Negative Borrow Duration
    login_sid = client.post("/api/auth/login", json={
        "email": "siddique2307010@stud.kuet.ac.bd",
        "password": "kuet1234"
    })
    tok_sid = login_sid.json()["access_token"]
    h_sid = {"Authorization": f"Bearer {tok_sid}"}

    res_neg_dur = client.post("/api/requests/", json={
        "item_id": 2,
        "duration_hours": -5
    }, headers=h_sid)
    record_finding(
        category="Schema Validation Requests",
        title="Negative borrow duration allowed (-5 hours)",
        attack_input="duration_hours=-5",
        status_code=res_neg_dur.status_code,
        expected_status="422 (Duration must be > 0)",
        details=f"Created request ID: {res_neg_dur.json().get('id')}" if res_neg_dur.status_code == 200 else res_neg_dur.text[:120],
        is_bug=(res_neg_dur.status_code == 200)
    )

    # 6.3 Standard type confusion & missing fields
    schema_cases = [
        ("Empty body {}", {}, 422),
        ("Missing password", {"name": "No Pwd", "email": "nopwd4707061@stud.kuet.ac.bd"}, 422),
        ("Missing email", {"name": "No Email", "password": "Password123!"}, 422),
        ("Missing name", {"email": "noname4707062@stud.kuet.ac.bd", "password": "Password123!"}, 422),
        ("Boolean for email", {"name": "Bool Email", "email": True, "password": "Password123!"}, 422),
        ("List for name", {"name": ["User"], "email": "listname4707063@stud.kuet.ac.bd", "password": "Password123!"}, 422),
        ("Integer for name", {"name": 12345, "email": "intname4707064@stud.kuet.ac.bd", "password": "Password123!"}, 422),
    ]

    for label, payload, exp_status in schema_cases:
        res = client.post("/api/auth/register", json=payload)
        is_bug = (res.status_code == 500)
        record_finding(
            category="Schema Validation Auth",
            title=label,
            attack_input=f"{label}",
            status_code=res.status_code,
            expected_status=f"{exp_status} (No 500)",
            details=res.text[:120],
            is_bug=is_bug
        )


def main():
    test_suite_emails()
    test_suite_unicode_and_boundaries()
    test_suite_sqli()
    test_suite_items_adversarial()
    test_suite_concurrency()
    test_suite_schema_validations()

    print("\n" + "=" * 60)
    print(f"TEST RUN COMPLETED: {results['total']} tests run")
    print(f"PASSED (HANDLED): {results['passed']} | FAILED (BUGS): {results['failed']}")
    print("=" * 60)

    with open(backend_dir / "adversarial_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
