# Handoff Report: Milestone 1 (Backend Core, Migration & Karma Implementation)

**Agent**: `worker_m1`  
**Role**: Implementer / QA / Specialist  
**Working Directory**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/worker_m1`  
**Target File**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/worker_m1/handoff.md`  
**Date**: 2026-09-10  

---

## 1. Observation

Direct observations from inspection and implementation:

1. **Landmark Data Porting & API**:
   - `Tanvir/kuet_data/kuet_landmarks.json` (439 lines, 15,523 bytes) was copied to `backend/app/data/kuet_landmarks.json`.
   - Contains 21 zones across academic, residential, hotspot, perimeter_700m, and admin categories, plus campus metadata (`center: [22.9006, 89.5024]`, `boundary_radius_meters: 700`).
   - Implemented `backend/app/routes/landmarks.py` exposing both `@router.get("")` and `@router.get("/")` to serve `{"success": true, "campus": ..., "zones": [...]}`.
   - Mounted `landmarks.router` in `backend/app/main.py:44`.

2. **Models and Schemas Updates**:
   - In `backend/app/models.py`:
     - `models.User`: added `karma = Column(Integer, default=100, nullable=False)`, retained `trust_score = Column(Float, default=100.0)`.
     - Removed standalone `unique=True` on `roll`, added composite `UniqueConstraint('batch', 'dept', 'roll', name='uq_user_batch_dept_roll')`.
     - `models.Item`: added `type = Column(String, default="lend")`, `specs = Column(Text, nullable=True)`, `tags = Column(JSON, default=list, nullable=True)`, `status = Column(String, default="available")`, `zone_id = Column(String, nullable=True)`, and properties `lat` and `lng`.
   - In `backend/app/schemas.py`:
     - Added `UserRegister` with `name`, `email`, `password`.
     - Added alias `UserCreate = UserRegister`.
     - Updated `UserOut` with `karma: int = 100` and `trust_score: Optional[float] = 100.0`.
     - Defined `TransactionOut` with `id`, `request_id`, `otp`, `qr_code`, `borrowed_at`, `returned_at`, `status`.
     - Updated `BorrowRequestOut` to include `transaction: Optional[TransactionOut] = None`.
     - Extended `ItemBase` and `ItemOut` with `type`, `specs`, `tags`, `status`, `zone_id`, `coords`, `lender_name`, `karma`, `roll`, `dept`, `batch`, with `@model_validator(mode='after')` normalization.

3. **KUET Email Validation & Roll Decoder (R3)**:
   - In `backend/app/routes/auth.py`:
     - Domain validation: `email_clean.endswith("@stud.kuet.ac.bd")` enforced; non-KUET emails raise `HTTPException(status_code=400, detail="Only @stud.kuet.ac.bd email addresses are allowed")`.
     - Roll decoder: Regex `r'(\d{2})(\d{2})(\d{3})$'` extracts `batch`, `dept`, `roll` from email prefix. If non-matching, raises `HTTPException(400)`.
     - Initialized users with `karma=100` and `trust_score=100.0`.
     - Added alias `GET /api/auth/current` returning `{ "success": True, "authenticated": True, "user": {...}, ... }`.

4. **KUET Karma Protocol (R4)**:
   - In `backend/app/routes/transactions.py` `POST /return/{request_id}`:
     - Compared `trans.returned_at` with `trans.borrowed_at + timedelta(hours=req.duration_hours)` using timezone-safe UTC datetimes.
     - On-time return: Owner receives +10 Karma (`owner.karma += 10`), Borrower receives +5 Karma (`borrower.karma += 5`).
     - Late return: Owner receives +10 Karma (`owner.karma += 10`), Borrower loses 30 Karma (`borrower.karma -= 30`).
     - Response returns JSON payload:
       ```json
       {
         "message": "Item returned successfully",
         "detail": "Return confirmed, item available again",
         "karma_updated": {
           "owner_gain": 10,
           "borrower_change": 5,
           "is_on_time": true
         }
       }
       ```

5. **Bugfixes & Cleanups**:
   - In `backend/app/routes/borrow_requests.py`:
     - `PUT /{request_id}/status`: parameter handling updated to accept status from either JSON body (`body: Optional[schemas.BorrowRequestStatusUpdate] = Body(None)`) or query parameter (`status: Optional[str] = Query(None)`).
     - Deleted orphaned file `backend/app/routes/requests.py`.
   - In `backend/app/routes/items.py`:
     - Dual-payload support: parses either `application/json` or `multipart/form-data` seamlessly and returns HTTP 201 Created.
     - Filter support: `category`, `type` (`lend`/`borrow`), `zone`/`zone_id`, `search`/`q`.
   - In `backend/app/database.py`:
     - Implemented `migrate_db()` to automatically upgrade existing SQLite schemas (adding `karma`, `type`, `specs`, `tags`, `status`, `zone_id`, and composite `UNIQUE (batch, dept, roll)`).
     - Anchored relative SQLite database path `campus_share.db` to the `backend/` directory.
   - In `backend/app/seed.py`:
     - Seeds 8 realistic student accounts and 10 campus items.
     - Hooked into `main.py` startup to auto-seed when items table is empty.

---

## 2. Logic Chain

1. **Data Migration & Routing**:
   - `Tanvir/kuet_data/kuet_landmarks.json` is required by both the MapLibre frontend and the Tanvir verification suite. Copying it to `backend/app/data/kuet_landmarks.json` and exposing it through `backend/app/routes/landmarks.py` ensures the FastAPI server serves the campus metadata independently while keeping `Tanvir/` intact until Milestone 3.
2. **Schema & Model Consistency**:
   - The frontend's `Transaction.jsx` was unable to render the Return button because `BorrowRequestOut` stripped `transaction` during serialization. Adding `transaction: Optional[TransactionOut] = None` resolves this.
   - The frontend's `Requests.jsx` sent `PUT /api/requests/{id}/status?status=accepted` without a body, which caused FastAPI to abort with HTTP 422. Making `body` optional and accepting `status` from query parameters allows both frontend and JSON clients to update status without errors.
3. **Roll Decoder & Auth**:
   - Requiring only `name`, `email`, `password` during registration and decoding `batch`, `dept`, `roll` using `r'(\d{2})(\d{2})(\d{3})$'` automates student profile generation and enforces the `@stud.kuet.ac.bd` domain constraint with HTTP 400.
   - Using `UniqueConstraint('batch', 'dept', 'roll')` prevents false-positive collisions across different departments with identical 3-digit roll numbers.
4. **Karma Calculation**:
   - Comparing `borrowed_at + timedelta(hours=duration_hours)` with `returned_at` (both normalized to UTC) provides a deterministic check for on-time vs late returns, applying +10 to owner, +5 for on-time borrower, and -30 for late borrower.
5. **Database Migration Safeguard**:
   - SQLite cannot alter existing constraints or automatically add columns through `Base.metadata.create_all()`. Implementing `migrate_db()` inspects existing tables using `PRAGMA table_info` and applies `ALTER TABLE` and table recreation where necessary, preserving existing records without database corruption.

---

## 3. Caveats

- **Tanvir Folder Retention**: Per `PROJECT.md` milestones, `Tanvir/` was preserved during Milestone 1 so existing verification suites can run against it. Complete deletion of `Tanvir/` is reserved for Milestone 3 after frontend React migration.
- **Python Runtime Environment**: In macOS sandboxed execution, outgoing TCP connections to localhost may be blocked by sandbox policy. Verification was executed via an in-process ASGI client (`ASGIClient`) that invokes the FastAPI application directly through the ASGI interface, as well as standalone test runs.

---

## 4. Conclusion

Milestone 1 is 100% complete and verified:
- All required backend endpoints (`/api/landmarks`, `/api/auth/register`, `/api/auth/current`, `/api/items`, `/api/requests/{id}/status`, `/api/transactions/return/{id}`) are fully implemented and conforming to `PROJECT.md` contracts.
- The KUET Roll Decoder accurately decodes `batch`, `dept`, and `roll` from student emails and initializes accounts with 100 Karma.
- The KUET Karma Protocol correctly updates scores (+10 owner, +5 on-time borrower, -30 late borrower).
- The database auto-migrates and auto-seeds on startup.
- All automated tests in `backend/test_m1.py` and `Tanvir/verify_campus_map.py` pass with zero failures.

---

## 5. Verification Method

To independently verify the Milestone 1 implementation:

1. **Run the Comprehensive Milestone 1 Verification Suite**:
   ```bash
   python3 backend/test_m1.py
   ```
   *Expected Output*:
   ```
   ==================================================
   STARTING COMPREHENSIVE MILESTONE 1 VERIFICATION
   ==================================================
   [TEST 1] Checking deletion of orphaned requests.py...
     --> PASS: backend/app/routes/requests.py does not exist.
   [TEST 2] Testing GET /api/landmarks (and trailing slash)...
     --> PASS: Landmarks endpoint returns 21 zones and 700m radius.
   [TEST 3] Testing Authentication & KUET Roll Decoder...
     --> PASS: Non-KUET email rejected with HTTP 400.
     --> PASS: Malformed KUET email rejected with HTTP 400.
     --> PASS: User registered with auto-decoded batch=25, dept=07, roll=028, karma=100.
     --> PASS: Composite unique constraint allows same roll in different department.
     --> PASS: GET /api/auth/current returns authenticated profile with karma and roll.
   [TEST 4] Testing Item Creation (JSON and Form) and Filters...
     --> PASS: Item created successfully via application/json.
     --> PASS: Item created successfully via multipart/form-data.
     --> PASS: Item filtering by type (lend/borrow), category, and search query verified.
   [TEST 5] Testing Borrow Request Status Update & Transaction schema...
     --> PASS: Borrow request accepted via query param ?status=accepted.
     --> PASS: BorrowRequestOut schema correctly includes transaction field.
   [TEST 6] Testing Handover and KUET Karma Protocol (+10 owner, +5 on-time, -30 late)...
     --> PASS: On-time return: Owner +10, Borrower +5.
     --> PASS: Late return: Owner +10, Borrower -30.
   ==================================================
   ALL MILESTONE 1 VERIFICATION TESTS PASSED SUCCESSFULLY!
   ==================================================
   ```

2. **Verify Tanvir Legacy Test Suite (95/95 passing)**:
   ```bash
   python3 Tanvir/verify_campus_map.py
   ```
   *Expected Output*:
   `TOTAL TESTS RUN: 95 | PASSED: 95 | FAILED: 0`

3. **Verify Database Seeding**:
   ```bash
   python3 -c "
   import sys; sys.path.insert(0, 'backend')
   from app.database import SessionLocal; from app import models
   db = SessionLocal()
   print('Users count:', db.query(models.User).count())
   print('Items count:', db.query(models.Item).count())
   print('Karma values:', [u.karma for u in db.query(models.User).limit(5)])
   db.close()
   "
   ```
   *Expected Output*:
   `Users count: 9+`, `Items count: 10+`, `Karma values: [100, ...]`

4. **Invalidation Conditions**:
   - Registering with non-`@stud.kuet.ac.bd` does not return HTTP 400.
   - Decoded user record lacks 100 base Karma or fails composite uniqueness.
   - `GET /api/landmarks` returns anything other than 21 zones and 700m radius.
   - `PUT /api/requests/{id}/status?status=accepted` returns HTTP 422.
   - Returning on-time fails to add +10 to owner or +5 to borrower, or returning late fails to deduct -30 from borrower.
