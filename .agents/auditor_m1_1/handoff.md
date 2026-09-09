# Forensic Audit Report: Milestone 1 Verification

**Agent**: `auditor_m1_1`  
**Role**: Forensic Auditor  
**Working Directory**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/auditor_m1_1`  
**Target**: Milestone 1 Backend Core, Data Migration & Karma Implementation  
**Integrity Mode**: `demo` (per `ORIGINAL_REQUEST.md`)  
**Verdict**: `CLEAN`

---

## Executive Summary

A forensic integrity audit was conducted on all Milestone 1 code deliverables in the `Forkathon2026-Team-KUET_MANTIS` repository. The audit covered static source analysis, AST/regex pattern inspections, runtime behavioral verification, on-disk SQLite persistence validation, and security access controls across the newly implemented endpoints.

**Final Verdict**: **`CLEAN`** — No evidence of hardcoded test results, facade implementations, pre-populated artifacts, test evasion, or integrity violations was found. Genuine business logic and persistent state transitions were verified empirically.

---

## 1. Forensic Phase Results

| # | Forensic Check | Result | Direct Empirical Evidence |
|---|---|:---:|---|
| 1 | **Hardcoded Test Results Detection** | **PASS** | Grep searches for test identifiers (`siddique2507028`, `student2501028`, `TI-84`, etc.) yielded zero occurrences in `backend/app`. Dynamic regex `r'(\d{2})(\d{2})(\d{3})$'` and dynamic SQLAlchemy updates execute on every request. |
| 2 | **Facade / Dummy Logic Detection** | **PASS** | No stubbed functions or constant-returning endpoints exist. Every endpoint queries or modifies the real SQLite database (`backend/campus_share.db`). Password hashing uses real bcrypt. |
| 3 | **Pre-populated Artifact Detection** | **PASS** | Workspace scan `find . \( -name '*.log' -o -name '*result*' -o -name '*output*' \)` returned 0 pre-populated verification logs or attestations. |
| 4 | **Runtime Behavioral Verification** | **PASS** | `backend/test_m1.py` passed all 6 test suites; `Tanvir/verify_campus_map.py` passed all 95 tests; independent auditor adversarial scripts passed with 100% accuracy. |
| 5 | **Database Persistence & ACID Properties** | **PASS** | Raw SQLite inspections via `sqlite3` confirmed records are written to physical disk storage, passwords stored hashed, unique constraints enforced, and updates reflected across separate DB connections. |
| 6 | **Access Control & Attack Surface Stress Test** | **PASS** | Attempting unauthorized transaction start, accept, verify, or return correctly returns HTTP 403 Forbidden. Invalid OTP returns HTTP 400. Duplicate returns return HTTP 400. |
| 7 | **KUET Karma Arithmetic Verification** | **PASS** | On-time return yields Owner +10, Borrower +5. Late return yields Owner +10, Borrower -30. Verified directly in SQLite rows before and after transactions. |

---

## 2. 5-Component Handoff Report

### 1. Observation

Direct observations from source inspection and execution:

1. **KUET Roll Decoder (`backend/app/routes/auth.py:10-25`)**:
   ```python
   def decode_kuet_email(email: str):
       email_clean = email.strip().lower()
       if not email_clean.endswith("@stud.kuet.ac.bd"):
           raise HTTPException(status_code=400, detail="Only @stud.kuet.ac.bd email addresses are allowed")
       local_part = email_clean.split("@")[0]
       match = re.search(r'(\d{2})(\d{2})(\d{3})$', local_part)
       if not match:
           raise HTTPException(status_code=400, detail="Invalid KUET student email...")
       batch, dept, roll = match.groups()
       return batch, dept, roll
   ```
   - Valid emails (`siddique2507028@stud.kuet.ac.bd`, `student1901099@stud.kuet.ac.bd`, `forensicaudit8809123@stud.kuet.ac.bd`) successfully extract `(batch, dept, roll)`.
   - Non-KUET emails (`outsider@gmail.com`, `user@kuet.ac.bd`) and emails without 7 trailing digits are rejected with HTTP 400.
   - Registration creates users with initial `karma=100` and `trust_score=100.0` (`backend/app/routes/auth.py:56-57`).
   - Composite constraint `UniqueConstraint('batch', 'dept', 'roll')` correctly permits students in different departments to share the same 3-digit roll while rejecting duplicate rolls within the same department.

2. **KUET Karma Protocol (`backend/app/routes/transactions.py:61-124`)**:
   - `request_return` verifies borrower authorization (`req.borrower_id == current_user.id`), checks `trans.status == "borrowed"`.
   - Due date calculated via `due_time = borrowed_at + timedelta(hours=duration)`.
   - Comparison `is_on_time = (now <= due_time)` assigns `owner_gain = 10` and `borrower_change = 5 if is_on_time else -30`.
   - Modifies `owner.karma` and `borrower.karma`, resets `item.is_available = True` and `item.status = "available"`.
   - An independent adversarial test created test accounts `karma_owner_7701111` and `karma_borrower_7702222`:
     - Initial Karma: Owner = 100, Borrower = 100.
     - On-time return: Owner = 110 (+10), Borrower = 105 (+5). Verified in DB.
     - Late return simulation: Owner = 120 (+10), Borrower = 75 (-30). Verified in DB.

3. **Landmarks & Seed Data (`backend/app/routes/landmarks.py`, `backend/app/data/kuet_landmarks.json`, `backend/app/seed.py`)**:
   - `GET /api/landmarks` and `GET /api/landmarks/` return `{"success": true, "campus": {"center": [22.9006, 89.5024], "boundary_radius_meters": 700, ...}, "zones": [...]}` with 21 zones.
   - Database auto-seeding populates 8 students and 10 campus items.

4. **Orphaned File Deletion**:
   - Verified that `backend/app/routes/requests.py` does not exist on disk.
   - `PUT /api/requests/{id}/status?status=accepted` operates without requiring a JSON body.

### 2. Logic Chain

1. From Observation 1, `decode_kuet_email` uses regular expression capture groups rather than a dictionary lookup of pre-seeded test emails. When tested against novel emails generated during the audit (`forensicaudit8809123@stud.kuet.ac.bd`), it extracted batch 88, department 09, roll 123, confirming genuine parsing logic.
2. From Observation 1 and raw SQLite connection queries, newly registered users produce real database rows with password hashes (bcrypt) and 100 Karma. Re-registering causes unique constraint enforcement, proving genuine DB persistence.
3. From Observation 2, Karma calculation depends on timestamps and request duration. Manipulating the `borrowed_at` timestamp of a transaction in the database directly triggered the late-return penalty (-30) and updated borrower Karma to 75, proving that the calculation is dynamic and not hardcoded to always return on-time status.
4. From Observation 2, unauthorized requests from third-party tokens (`hacker_token`) were blocked with HTTP 403 Forbidden across all sensitive transaction phases, confirming genuine authorization checks.
5. Therefore, the implementation is authentic, complete, robust, and free of cheating or integrity violations.

### 3. Caveats

- In macOS sandboxed execution, outgoing TCP loopback connections to uvicorn servers may be restricted by sandbox network policy. Runtime verification was conducted via FastAPI's native ASGI interface (`ASGIClient`) and direct SQLite queries, which provides identical code-path execution without relying on unauthenticated network sockets.
- As planned in `PROJECT.md`, the `Tanvir/` legacy directory is retained until Milestone 3 frontend migration is complete; its presence is an approved architectural dependency for backward compatibility and not an integrity violation.

### 4. Conclusion

**Verdict**: **`CLEAN`**

All Milestone 1 deliverables comply fully with `ORIGINAL_REQUEST.md` (Demo Mode) and `PROJECT.md` specifications. There are no hardcoded responses, no dummy facades, no pre-populated artifacts, and no test bypasses. Milestone 1 is verified and approved to proceed to Milestone 2.

### 5. Verification Method

To independently reproduce the forensic verification:

1. **Run Milestone 1 Test Suite**:
   ```bash
   python3 backend/test_m1.py
   ```
   *Expected*: `ALL MILESTONE 1 VERIFICATION TESTS PASSED SUCCESSFULLY!`

2. **Run Tanvir Legacy Verification Suite**:
   ```bash
   python3 Tanvir/verify_campus_map.py
   ```
   *Expected*: `TOTAL TESTS RUN: 95 | PASSED: 95 | FAILED: 0`

3. **Run Independent Forensic Stress Test**:
   ```bash
   python3 -c "
   import sys; sys.path.insert(0, 'backend')
   import sqlite3
   from app.routes.auth import decode_kuet_email
   assert decode_kuet_email('test2507028@stud.kuet.ac.bd') == ('25', '07', '028')
   conn = sqlite3.connect('backend/campus_share.db')
   c = conn.cursor()
   c.execute('SELECT COUNT(*) FROM users')
   print('Verified users count in DB:', c.fetchone()[0])
   c.execute('SELECT COUNT(*) FROM items')
   print('Verified items count in DB:', c.fetchone()[0])
   conn.close()
   "
   ```

4. **Invalidation Conditions**:
   - Any registration with non-KUET email does not return HTTP 400.
   - User creation fails to default to 100 Base Karma.
   - On-time return fails to add +10 to owner and +5 to borrower.
   - Late return fails to deduct -30 from borrower.
   - Item availability does not toggle from False back to True upon return.

