# Reviewer Handoff Report: Milestone 1 Verification & Adversarial Audit

**Agent**: `reviewer_m1_2`  
**Roles**: Reviewer, Critic  
**Working Directory**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/reviewer_m1_2`  
**Target File**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/reviewer_m1_2/handoff.md`  
**Verdict**: **APPROVE**  
**Date**: 2026-09-10  

---

## Review Summary

**Verdict**: **APPROVE**

Milestone 1 satisfies all functional, architectural, database integrity, and security specifications. Zero integrity violations, zero facade implementations, and zero hardcoded shortcuts were found. All edge cases and boundary conditions passed exhaustive adversarial stress testing.

---

## 1. Observation

Direct observations from inspection and execution:

1. **Test Suite Execution**:
   - Executed `python3 backend/test_m1.py`:
     - Test 1 (deletion of orphaned `requests.py`): PASS.
     - Test 2 (`GET /api/landmarks` with 21 zones and 700m radius): PASS.
     - Test 3 (Non-KUET rejection, roll decoder, composite uniqueness, base Karma 100): PASS.
     - Test 4 (JSON and Form item creation, filtering): PASS.
     - Test 5 (Borrow request accept via query param, `BorrowRequestOut.transaction` serialization): PASS.
     - Test 6 (Handover OTP verification, on-time +10/+5, late return +10/-30): PASS.
     - Result: `ALL MILESTONE 1 VERIFICATION TESTS PASSED SUCCESSFULLY!`.
   - Executed `python3 Tanvir/verify_campus_map.py`:
     - Total Tests: 95, Passed: 95, Failed: 0. Score: 10.0 / 10.0.

2. **Database Schema & Robustness Inspection**:
   - SQLite master inspection of `backend/campus_share.db`:
     - Table `users`: defined with `UNIQUE (batch, dept, roll)`, auto-indexed by `sqlite_autoindex_users_2`, and `email VARCHAR NOT NULL UNIQUE` indexed by `ix_users_email`.
     - Columns `karma INTEGER DEFAULT 100`, `trust_score FLOAT DEFAULT 100.0`, `batch`, `dept`, `roll` confirmed present.
     - Table `items`: columns `type VARCHAR DEFAULT 'lend'`, `specs TEXT`, `tags JSON`, `status VARCHAR DEFAULT 'available'`, `zone_id VARCHAR` confirmed present.
     - Table `transactions`: `request_id`, `otp`, `qr_code`, `borrowed_at`, `returned_at`, `status` confirmed present.

3. **Code Implementation Audit**:
   - `backend/app/routes/auth.py`:
     - Lines 10–25: `decode_kuet_email(email)` cleans input with `.strip().lower()`, validates `.endswith("@stud.kuet.ac.bd")` (raising HTTP 400), and parses trailing 7 digits using regex `r'(\d{2})(\d{2})(\d{3})$'`.
     - Lines 28–63: `register()` performs pre-validation for email uniqueness and composite roll uniqueness (`models.User.batch == batch, models.User.dept == dept, models.User.roll == roll`), initialises `karma=100`, `trust_score=100.0`.
   - `backend/app/routes/transactions.py`:
     - Lines 61–123: `request_return()` enforces `req.borrower_id == current_user.id`, validates `trans.status == "borrowed"`, calculates `is_on_time = (now <= due_time)` using UTC datetimes, applies `owner_gain = 10`, `borrower_change = 5 if is_on_time else -30`, updates DB fields, and marks `item.is_available = True` and `item.status = "available"`.
   - `backend/app/routes/borrow_requests.py`:
     - Lines 8–46: Prevents requesting own item (`item.owner_id == current_user.id`) and duplicate pending requests.
     - Lines 60–118: Accepts status from body or query, enforces authorization (`owner_id == current_user.id`), verifies availability before accept, auto-declines conflicting pending requests for the same item.
   - `backend/app/routes/items.py`:
     - Lines 54–156: Dual-payload parser for `application/json` and `multipart/form-data`, returns HTTP 201 with populated item schema.

4. **Adversarial Stress Testing**:
   - Created and executed `.agents/reviewer_m1_2/test_adversarial_m1.py` with 14 attack scenarios.
   - All 14 scenarios passed with 0 failures:
     - Subdomain spoofing (`attacker@stud.kuet.ac.bd.attacker.com`): rejected with 400.
     - Non-student KUET domain (`faculty@kuet.ac.bd`): rejected with 400.
     - Short roll (< 7 digits), alphabetic/symbol roll: rejected with 400.
     - Email normalization (uppercase and whitespace): correctly normalized and decoded.
     - Composite uniqueness: duplicate roll in same dept blocked; same roll in different dept permitted; same roll in different batch permitted.
     - State machine security: unauthorized accept blocked (403), unauthorized handover start blocked (403), wrong OTP blocked (400), unauthorized return blocked (403), replay return blocked (400).
     - State restoration: returned items immediately restored to `is_available = True` and `status = "available"`.

---

## 2. Logic Chain

1. **Requirement 3 (Authentication & Roll Decoder)**:
   - Observation: `decode_kuet_email` rejects any domain other than `@stud.kuet.ac.bd` with HTTP 400 and extracts batch, dept, roll using `(\d{2})(\d{2})(\d{3})$`.
   - Observation: SQLite schema contains `UNIQUE (batch, dept, roll)` and `register` checks both email and composite uniqueness before insertion.
   - Deduction: Non-KUET emails cannot register; malformed IDs cannot register; identical student IDs across different departments do not clash; identical student IDs within the same department cannot be registered twice. Requirement R3 is fully satisfied.

2. **Requirement 4 (KUET Karma Rating System)**:
   - Observation: Registrations initialise with `karma = 100`.
   - Observation: `transactions.py` compares `now` with `trans.borrowed_at + timedelta(hours=duration_hours)`. On-time yields `owner.karma += 10`, `borrower.karma += 5`. Late return yields `owner.karma += 10`, `borrower.karma -= 30`.
   - Observation: Real transactions tested in `test_m1.py` and `test_adversarial_m1.py` verified database persistence across multiple state transitions.
   - Deduction: The KUET Karma protocol logic is completely implemented and resilient to manipulation. Requirement R4 is fully satisfied.

3. **Integrity & Code Quality**:
   - Observation: Code contains no mock bypasses, no hardcoded conditionals matching test credentials, and no dummy implementations.
   - Observation: All 95 legacy tests and 6 comprehensive new tests pass against real database instances and real FastAPI routers.
   - Deduction: The implementation is genuine, sound, and ready for Milestone 2.

---

## 3. Caveats

- **Timezone Normalisation**: SQLite does not store tzinfo by default. `transactions.py` explicitly guards against naive datetimes via `if borrowed_at.tzinfo is None: borrowed_at = borrowed_at.replace(tzinfo=timezone.utc)`. This design choice is robust for SQLite, but if migrating to PostgreSQL in the future, `DateTime(timezone=True)` should be maintained.
- **Tanvir Folder Cleanup**: Per `PROJECT.md`, the root `Tanvir/` directory is intentionally kept until Milestone 3 to ensure regression testing against the legacy suite passes during frontend development.

---

## 4. Conclusion

Milestone 1 implementation is exemplary. All criteria specified in `ORIGINAL_REQUEST.md` and `PROJECT.md` for Milestone 1 are satisfied.
- Non-KUET emails rejected with HTTP 400: **VERIFIED**
- Roll decoder and composite uniqueness: **VERIFIED**
- KUET Karma Protocol (+10, +5, -30) & 100 Base Karma: **VERIFIED**
- Database robustness, migrations, and model constraints: **VERIFIED**
- Deletion of orphaned `requests.py` router: **VERIFIED**

**Final Verdict**: **APPROVE**

---

## 5. Verification Method

To independently reproduce and verify this review:

1. **Run Comprehensive Milestone 1 Test Suite**:
   ```bash
   python3 backend/test_m1.py
   ```
   *Expected*: All 6 test suites pass with code 0.

2. **Run Reviewer Adversarial Stress-Test Suite**:
   ```bash
   python3 .agents/reviewer_m1_2/test_adversarial_m1.py
   ```
   *Expected*: All 14 adversarial checks (spoofing, composite uniqueness, OTP security, replay protection, Karma calculation) pass with code 0.

3. **Verify Legacy Regression Compatibility**:
   ```bash
   python3 Tanvir/verify_campus_map.py
   ```
   *Expected*: `TOTAL TESTS RUN: 95 | PASSED: 95 | FAILED: 0`.

4. **Inspect SQLite Schema**:
   ```bash
   python3 -c "
   import sqlite3
   con = sqlite3.connect('backend/campus_share.db')
   cur = con.cursor()
   print(cur.execute(\"SELECT sql FROM sqlite_master WHERE type='table' AND name='users'\").fetchone()[0])
   con.close()
   "
   ```
   *Expected*: Output contains `karma INTEGER DEFAULT 100` and `UNIQUE (batch, dept, roll)`.

---

## Adversarial Challenge Report

### Challenge Summary
**Overall Risk Assessment**: **LOW**

### Challenges Evaluated
1. **Domain Spoofing Attack (`attacker@stud.kuet.ac.bd.attacker.com`)**:
   - Attack scenario: Attacker attempts to register using an email ending in attacker domain while containing target domain in prefix.
   - Result: HTTP 400 rejected. Mitigation verified.
2. **Roll Collision Across Departments (`2401888` vs `2407888`)**:
   - Attack scenario: Two students in different departments have the same roll number.
   - Result: Both succeed. Composite uniqueness allows valid cross-department rolls.
3. **Identity Impersonation (Same Roll in Same Dept with Alternate Email)**:
   - Attack scenario: Attacker registers with different email prefix matching an existing student's roll and dept.
   - Result: HTTP 400 rejected (`Roll number already registered for this batch and department`).
4. **Replay Return / Karma Inflation Attack**:
   - Attack scenario: Borrower calls `POST /api/transactions/return/{id}` multiple times to inflate lender's Karma (+10 per call) and borrower's Karma (+5 per call).
   - Result: HTTP 400 rejected on subsequent calls (`Item not currently borrowed`).
5. **Unauthorized Transaction State Transition**:
   - Attack scenario: Attacker attempts to start handover on an unaccepted request or verify handover with wrong/missing OTP.
   - Result: Blocked with HTTP 400/403.
6. **Simultaneous Request Race Condition**:
   - Attack scenario: Two users request the same item; owner accepts one.
   - Result: Owner acceptance automatically declines all other pending requests and marks item unavailable.

### Stress Test Results Summary
- 14 adversarial stress test scenarios executed.
- 0 vulnerabilities discovered.
- 100% pass rate.
