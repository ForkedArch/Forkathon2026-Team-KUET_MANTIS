# Dispatch: Worker M1 (Backend Core, Migration & Karma Implementation)

## Objective
Implement all backend changes for Milestone 1 (R1 Data/Landmarks Porting, R3 Auth & KUET Roll Decoder, R4 KUET Karma Protocol, and Schema Bugfixes).

## Scope Boundaries & Exclusive File Ownership
Worker M1 exclusively owns:
- `backend/app/data/kuet_landmarks.json` (copy from `Tanvir/kuet_data/kuet_landmarks.json`)
- `backend/app/routes/landmarks.py` (new router)
- `backend/app/routes/auth.py`
- `backend/app/routes/items.py`
- `backend/app/routes/borrow_requests.py`
- `backend/app/routes/transactions.py`
- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/main.py`
- `backend/app/database.py`
- `backend/app/seed.py` (new)
- Deletion of `backend/app/routes/requests.py`
- `backend/test_m1.py` or unit test verification scripts

Do NOT modify frontend files in this milestone.

## Key Technical Specifications
1. **Data & Landmarks API (R1)**:
   - Create `backend/app/data/` and copy `Tanvir/kuet_data/kuet_landmarks.json`.
   - Implement `backend/app/routes/landmarks.py` exposing `GET /api/landmarks` (with both trailing and non-trailing slashes).
   - Mount `landmarks.router` in `main.py`.
2. **Models & Schemas**:
   - `models.User`: add `karma = Column(Integer, default=100, nullable=False)`. Keep `trust_score = Column(Float, default=100.0)`. Update `roll` uniqueness constraint to composite `UniqueConstraint('batch', 'dept', 'roll')`.
   - `models.Item`: add `type = Column(String, default="lend")`, `specs = Column(Text, nullable=True)`, `tags = Column(JSON, default=list, nullable=True)`, `status = Column(String, default="available")`, `zone_id = Column(String, nullable=True)`.
   - `schemas.UserRegister`: accept only `name`, `email`, `password`.
   - `schemas.UserOut`: expose `karma: int = 100`, `trust_score`.
   - `schemas.TransactionOut`: define model with `id`, `request_id`, `otp`, `qr_code`, `status`, `borrowed_at`, `returned_at`.
   - `schemas.BorrowRequestOut`: include `transaction: Optional[TransactionOut] = None`.
   - `schemas.ItemOut`: provide normalized coordinates `lat`, `lng`, `coords`, `lender_name`, `roll`, `karma`.
3. **Authentication & Roll Decoder (R3)**:
   - Require `@stud.kuet.ac.bd` domain in `register`, raise HTTP 400 if invalid.
   - Extract `batch`, `dept`, `roll` using regex `r'(\d{2})(\d{2})(\d{3})$'` on local part.
   - Populate `batch`, `dept`, `roll`, `karma=100` on new user.
   - Add legacy compatibility endpoint `GET /api/auth/current`.
4. **Karma Protocol & Transactions (R4)**:
   - In `backend/app/routes/transactions.py` `POST /return/{request_id}`:
     - Compare `trans.returned_at` with `trans.borrowed_at + timedelta(hours=req.duration_hours)` (timezone-safe UTC).
     - Owner: +10 Karma (`owner.karma += 10`).
     - On-time borrower: +5 Karma (`borrower.karma += 5`).
     - Late borrower: -30 Karma (`borrower.karma -= 30`).
     - Return JSON response with `karma_updated: {"owner_gain": 10, "borrower_change": 5 or -30, "is_on_time": bool}`.
5. **Bugfixes & Cleanups**:
   - `backend/app/routes/borrow_requests.py`: update `update_request_status` to accept `status` from either JSON body or query param `?status=...`.
   - Delete orphaned `backend/app/routes/requests.py`.
   - `backend/app/routes/items.py`: support both JSON body and multipart form data in `POST /api/items/`, and support query filters `type`, `category`, `search`/`q`, `zone`.
   - Database migration/startup: run SQLite `ALTER TABLE users ADD COLUMN karma INTEGER DEFAULT 100` and items table columns if missing.
   - `seed.py`: seed 8 students and 10 campus items. Auto-seed on startup when items count == 0.

## Mandatory Verification
Run a verification script testing:
1. Registration with non-KUET email -> HTTP 400.
2. Registration with `siddique52507028@stud.kuet.ac.bd` -> Batch="25", Dept="07", Roll="028", Karma=100.
3. Landmarks endpoint -> 21 zones, 700m radius.
4. Item creation (both JSON and form) and list filtering by type (lend/borrow).
5. Borrow request status update via query param and body.
6. Handover and Return -> Karma calculations (+10 owner, +5 on-time, -30 late).

Write handoff report to:
`/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/worker_m1/handoff.md`

## 2026-09-09T21:51:14Z
Task: Implement Milestone 1 (Backend Core, Migration & Karma Implementation).
See detailed instructions above.
