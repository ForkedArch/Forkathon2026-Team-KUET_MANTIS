# Explorer Survey 3: Backend Architecture & Evaluation Infrastructure Report

## Executive Summary
This report presents an in-depth architectural survey of the FastAPI backend (`backend/`), existing evaluation scripts (`Tanvir/verify_campus_map.py`), authentication and session logic, transaction lifecycle and karma system, and assets to port from `Tanvir/` into `backend/`. Multiple critical runtime bugs and architectural discrepancies were uncovered between the backend schemas and frontend expectations, and a concrete roadmap is provided for satisfying requirements R1, R3, R4, and R5.

---

## 1. Observation

### 1.1 Backend Directory Structure and Entry Points
Direct inspection of `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend/` reveals:
- **Application Directory (`backend/app/`)**:
  - `main.py` (Lines 1–42): Instantiates `FastAPI(title="CampusShare KUET API")`, adds CORS middleware with `ALLOWED_ORIGINS` (default `http://localhost:5173`), mounts `/uploads` via `StaticFiles(directory=upload_dir)`, binds database tables via `Base.metadata.create_all(bind=engine)`, and includes routers: `auth.router`, `items.router`, `borrow_requests.router`, `chat.router`, `transactions.router`.
  - `database.py` (Lines 1–23): Configures SQLAlchemy engine using `os.getenv("DATABASE_URL", "sqlite:///./campus_share.db")` with `connect_args={"check_same_thread": False}`. Provides `SessionLocal` and `get_db()` dependency generator.
  - `models.py` (Lines 1–93): Defines 5 SQLAlchemy ORM models: `User`, `Item`, `BorrowRequest`, `Transaction`, and `Message`.
  - `schemas.py` (Lines 1–118): Defines Pydantic schemas using Pydantic v2 `ConfigDict(from_attributes=True)`.
  - `auth.py` (Lines 1–74): Implements `pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")`, `HTTPBearer(auto_error=True)`, `create_access_token()`, and `get_current_user()` dependency checking JWT payload `"sub"` against `models.User.id`.
- **Routers (`backend/app/routes/`)**:
  - `auth.py`: `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`.
  - `items.py`: `GET /api/items/`, `POST /api/items/` (expects `Form(...)` parameters and optional `UploadFile`), `GET /api/items/{item_id}`, `PUT /api/items/{item_id}`, `DELETE /api/items/{item_id}`.
  - `borrow_requests.py`: `POST /api/requests/`, `GET /api/requests/me`, `PUT /api/requests/{request_id}/status` (expects `BorrowRequestStatusUpdate` body).
  - `requests.py`: **Duplicate/Orphaned file** (Lines 1–72) not imported or mounted in `main.py`. Uses `status: str` query parameter instead of body.
  - `transactions.py`: `POST /api/transactions/start`, `POST /api/transactions/verify`, `POST /api/transactions/return/{request_id}`.
  - `chat.py`: `GET /api/chat/{request_id}/messages`, `POST /api/chat/{request_id}/messages`.
- **Utilities (`backend/app/utils/`)**:
  - `file_upload.py` (Lines 1–63): Handles image uploads, validates MIME types (`image/jpeg`, `image/png`, `image/webp`), enforces 5 MB limit.
  - `qr_code.py` (Lines 1–19): Generates Base64 encoded PNG data URLs for OTP QR codes.
- **Database & Environment**:
  - Database file: `backend/campus_share.db` (53,248 bytes). SQLite database contains tables: `users`, `items`, `borrow_requests`, `transactions`, `messages`.
  - Current contents: 1 user (`anik52507030@stud.kuet.ac.bd`, `Mugdha Sarker Anik`, dept `CSE`, batch `2025`, roll `2507030`, trust_score `4.5`), 0 items, 0 requests, 0 transactions, 0 messages.
- **Dependencies (`backend/requirements.txt`)**:
  - Contains: `fastapi==0.115.6`, `uvicorn[standard]==0.34.0`, `sqlalchemy==2.0.36`, `python-jose[cryptography]==3.3.0`, `passlib[bcrypt]==1.7.4`, `bcrypt==4.0.1`, `python-multipart==0.0.20`, `aiosqlite==0.20.0`, `Pillow==11.0.0`, `qrcode==8.0`, `pydantic-settings==2.6.1`, `email-validator==2.2.0`, `python-dotenv==1.0.1`.
  - Note: `backend/venv` directory exists in the workspace but contains Windows binaries (`Scripts/` and `Lib/`, `pyvenv.cfg` targeting Windows Python).

---

### 1.2 Authentication System & KUET Roll Decoder (R3)
- **Current Registration Endpoint (`backend/app/routes/auth.py` lines 8–30)**:
  ```python
  @router.post("/register", response_model=schemas.UserOut)
  def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
      db_user = db.query(models.User).filter(models.User.email == user.email).first()
      if db_user:
          raise HTTPException(status_code=400, detail="Email already registered")
      db_roll = db.query(models.User).filter(models.User.roll == user.roll).first()
      if db_roll:
          raise HTTPException(status_code=400, detail="Roll number already registered")
      hashed = auth.get_password_hash(user.password)
      new_user = models.User(
          email=user.email,
          name=user.name,
          dept=user.dept,
          batch=user.batch,
          roll=user.roll,
          hashed_password=hashed,
      )
  ```
- **Current `UserCreate` Schema (`backend/app/schemas.py` lines 6–14)**:
  ```python
  class UserBase(BaseModel):
      email: EmailStr
      name: str
      dept: str
      batch: str
      roll: str

  class UserCreate(UserBase):
      password: str
  ```
  `UserCreate` currently mandates that the client manually supply `dept`, `batch`, and `roll`.
- **Current Frontend Register Form (`frontend/src/App.jsx` lines 44–73)**:
  Directly asks the student for 6 fields: `email`, `name`, `dept`, `batch`, `roll`, `password`.
- **Current User Model (`backend/app/models.py` lines 11–26)**:
  Fields: `id` (int), `email` (string, unique), `name` (string), `dept` (string), `batch` (string), `roll` (string, unique), `hashed_password` (string), `is_verified` (bool), `trust_score` (float, default 4.5), `total_lends` (int, default 0), `total_borrows` (int, default 0), `created_at` (datetime).
- **R3 Requirements (`ORIGINAL_REQUEST.md` lines 27–29, 43–46)**:
  - Registration form must ONLY accept: `Full Name`, `Password`, and `Email`.
  - Email MUST end with `@stud.kuet.ac.bd`. Any non-KUET email must fail with an HTTP error.
  - The backend must automatically parse and store `Batch`, `Department`, and `Roll` number from the email prefix (e.g., `siddique52507028@stud.kuet.ac.bd` -> `Batch=25, Dept=07, Roll=028`).

---

### 1.3 Borrow, Lending, Transaction, and Karma System (R4)
- **Current Item Model (`backend/app/models.py` lines 31–49)**:
  Columns: `id`, `title`, `category`, `description`, `condition`, `image_url`, `latitude`, `longitude`, `zone`, `is_available`, `owner_id`, `created_at`.
  Missing columns present in `Tanvir/app.py`: `type` (lend vs borrow beacon), `specs`, `tags`.
- **Current Transaction Lifecycle (`backend/app/routes/transactions.py`)**:
  - `POST /api/transactions/start`: Owner initiates handover for accepted request. Generates 4-digit OTP and QR code Base64. Status becomes `"pending"`.
  - `POST /api/transactions/verify`: Borrower submits OTP. If matched, `trans.status = "borrowed"`, `trans.borrowed_at = datetime.now(timezone.utc)`.
  - `POST /api/transactions/return/{request_id}`: Borrower requests return.
    ```python
    trans.status = "returned"
    trans.returned_at = datetime.now(timezone.utc)
    item.is_available = True
    owner.total_lends += 1
    owner.trust_score = min(5.0, owner.trust_score + 0.05)
    borrower.total_borrows += 1
    borrower.trust_score = min(5.0, borrower.trust_score + 0.03)
    req.status = "completed"
    ```
- **R4 Requirements (`ORIGINAL_REQUEST.md` lines 30–32, 47–50)**:
  - Replace generic 5.0 trust score with "KUET Karma Rating System".
  - Users start with 100 Base Karma (`karma = 100`).
  - Completed transaction logic:
    - Successfully lending adds **+10** to owner (`owner.karma += 10`).
    - Returning on time adds **+5** to borrower (`borrower.karma += 5`).
    - Returning late deducts **-30** from borrower (`borrower.karma -= 30`).
  - On-time vs late calculation: Duration was specified in `BorrowRequest.duration_hours`. Due timestamp is `trans.borrowed_at + timedelta(hours=req.duration_hours)`. If `trans.returned_at > due_time`, return is late; otherwise on time.

---

### 1.4 Existing Evaluation and Test Scripts
- **Found in Repository**:
  - `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/Tanvir/verify_campus_map.py` (435 lines): Automated verification suite for the standalone `Tanvir/` folder. Tested 95 assertions across landmarks, 700m perimeter, clean map, UI layout, mock users/items, manual pinpointing, modular auth, and REST API. Running `python3 Tanvir/verify_campus_map.py` completed with 95/95 PASS and estimated score 10.0 / 10.0.
- **Evaluation Infrastructure Gap**:
  - There is currently **NO** test script in `backend/` (no `pytest`, no `tests/` directory).
  - There is **NO** 20-point Agent-as-Judge rubric script in the project root.
  - Requirement R5 specifically mandates an Agent-as-Judge evaluator running against a 20-point Problem Statement Rubric (4 pts Integration, 4 pts UI Layout, 4 pts Auth, 4 pts Karma, 4 pts End-to-End User Experience) with a threshold >= 18/20.

---

### 1.5 Endpoints and Static Data in `Tanvir/` to Port into `backend/`
- **Static Data (`Tanvir/kuet_data/kuet_landmarks.json`, 439 lines)**:
  - `campus`: center `[22.9006, 89.5024]`, `boundary_radius_meters: 700`, `zoom_default: 16.5`.
  - `zones`: 21 campus zones/landmarks (CSE, EEE, ME, Civil, Central Library, Central Cafeteria, 7 halls, Gates, etc.).
  - `sample_active_items`: 10 simulated items (7 offers to lend, 3 demand beacons) with realistic KUET student users (`Siddique Ahmed`, `Tanvir Rahman`, `Anik Sen`, `Anonnya Roy`, `Rafiul Islam`, `Mahir Faisal`, `Sadia Afrin`, `Farhan Kabir`).
- **Endpoints in `Tanvir/app.py`**:
  - `GET /api/landmarks`: Returns `{ "success": True, "campus": ..., "zones": [...] }`.
  - `GET /api/items`: Filters by `category`, `type` (`lend` vs `borrow`), and search query `q`. Returns `{ "success": True, "count": N, "items": [...] }`.
  - `POST /api/items`: Accepts JSON payload for item creation.
  - `GET /api/auth/current`: Returns `{ "success": True, "authenticated": True, "user": {...} }`.
  - `GET /kuet_data/*`: Serves static data JSON.
- **Contract (`Tanvir/export_contracts/campus_map_contract.ts`)**:
  - Defines TypeScript interfaces `KUETLandmark`, `MapItemPin`, `GodsEyeMapProps`.

---

### 1.6 Critical Bugs and Integration Discrepancies Discovered

#### Bug 1: Missing `transaction` field in `BorrowRequestOut` schema blocks Return in UI
- **Location**: `backend/app/schemas.py` lines 66–82 vs `frontend/src/pages/Transaction.jsx` line 102.
- **Details**: `models.BorrowRequest` has relationship `transaction = relationship("Transaction", ...)`. However, `schemas.BorrowRequestOut` does NOT include `transaction: Optional[TransactionOut] = None`.
- **Impact**: When `GET /api/requests/me` returns `BorrowRequestOut` objects, FastAPI strips the `transaction` attribute. In `Transaction.jsx`, `request?.transaction?.status === 'borrowed'` will evaluate to `undefined === 'borrowed'` (falsy), so the "Request Return" button is NEVER rendered. The return flow cannot be completed from the frontend.

#### Bug 2: Method and Body Mismatch on `PUT /api/requests/{request_id}/status`
- **Location**: `backend/app/routes/borrow_requests.py` line 62 vs `frontend/src/pages/Requests.jsx` line 18.
- **Details**: `borrow_requests.py` expects a JSON body: `body: schemas.BorrowRequestStatusUpdate`. In `frontend/src/pages/Requests.jsx`, the code calls: `await api.put('/requests/${requestId}/status?status=${status}');` with no request body.
- **Impact**: FastAPI returns HTTP 422 Unprocessable Entity (`body missing`), blocking request acceptance/rejection from the frontend.

#### Bug 3: `backend/app/routes/items.py` Only Accepts `multipart/form-data`
- **Location**: `backend/app/routes/items.py` lines 30–41.
- **Details**: `create_item` parameters are all declared as `Form(...)`.
- **Impact**: Any API test, judge script, or Tanvir client sending `Content-Type: application/json` fails with HTTP 422.

#### Bug 4: Orphaned Route File `backend/app/routes/requests.py`
- **Location**: `backend/app/routes/requests.py`.
- **Details**: Not registered in `backend/app/main.py`. It is an outdated duplicate of `borrow_requests.py`.

#### Bug 5: `backend/venv` Windows Artifacts on macOS
- **Location**: `backend/venv/Scripts`, `backend/venv/Lib`.
- **Details**: The committed venv contains Windows batch scripts and libraries, not runnable on macOS. Standard system Python 3.10 is installed, but backend dependencies need a clean virtual environment.

---

## 2. Logic Chain

### 2.1 Logic: Porting `Tanvir/` to `backend/` and `frontend/` (R1)
1. **Observation**: `Tanvir/app.py` serves `/api/landmarks`, `/api/items`, `/api/auth/current`, and static files from `kuet_data/kuet_landmarks.json`. `Tanvir/index.html` implements MapLibre GL with a 700m perimeter ring.
2. **Deduction**:
   - `kuet_landmarks.json` should be placed into `backend/app/data/kuet_landmarks.json`.
   - A new router `backend/app/routes/landmarks.py` (or endpoints in `items.py`) must serve `GET /api/landmarks` returning `{ "success": True, "campus": ..., "zones": [...] }`.
   - The database should seed the 10 items and 8 users from `kuet_landmarks.json` so that initial items with student credentials exist immediately upon startup.
   - Once the React frontend imports and renders MapLibre GL and the backend serves all endpoints, `Tanvir/` can be safely deleted, fulfilling R1.

### 2.2 Logic: KUET Email Roll Decoder (R3)
1. **Observation**: `ORIGINAL_REQUEST.md` states:
   "It should only accept Full Name, Password, and Email. The Email must end with `@stud.kuet.ac.bd`. The backend must automatically parse and store the Batch, Department, and Roll number from the email prefix (e.g., `siddique52507028@stud.kuet.ac.bd` -> Batch=25, Dept=07, Roll=028) instead of asking the user to type them."
2. **Analysis of Prefix Pattern**:
   - Example 1: `siddique52507028@stud.kuet.ac.bd`: name prefix `siddique`, degree code `5` (undergraduate B.Sc. Eng.), batch `25`, dept `07` (CSE), roll `028`.
   - Example 2 (from DB): `anik52507030@stud.kuet.ac.bd`: name prefix `anik`, degree code `5`, batch `25`, dept `07` (CSE), roll `030`.
   - In all KUET student emails, the trailing 7 digits of the local part are `YY` (2-digit batch) + `DD` (2-digit dept code) + `RRR` (3-digit roll).
3. **Regex & Extraction**:
   - Validation: `email.endswith("@stud.kuet.ac.bd")`.
   - Extraction: `re.search(r"(\d{2})(\d{2})(\d{3})$", local_part)`.
   - Group 1: `batch = match.group(1)` (e.g., `"25"`).
   - Group 2: `dept = match.group(2)` (e.g., `"07"`, with optional department name mapping `"07 (CSE)"`).
   - Group 3: `roll = match.group(3)` (e.g., `"028"`, or full roll `"2507028"`).
4. **Database Constraint Resolution**:
   - In `models.py`, `roll = Column(String, unique=True)`. If `roll` stores `"028"`, two students with roll 028 from different departments would conflict.
   - Solution: Store `roll="028"` with `UniqueConstraint("batch", "dept", "roll")`, or store `roll="2507028"` while exposing `roll_number="028"`, `batch="25"`, `dept="07"`.

### 2.3 Logic: KUET Karma Rating Protocol (R4)
1. **Observation**:
   - Base karma: New users must start with 100 Base Karma.
   - Return completed: Lender receives **+10**.
   - Borrower return on time: Borrower receives **+5**.
   - Borrower return late: Borrower receives **-30**.
2. **Mathematical Definition of On-Time vs Late**:
   - Let $T_{\text{borrow}} = \text{trans.borrowed\_at}$ (UTC timestamp set on verify handover).
   - Let $D = \text{req.duration\_hours}$ (set on borrow request creation).
   - Let $T_{\text{due}} = T_{\text{borrow}} + \text{timedelta}(\text{hours}=D)$.
   - Let $T_{\text{return}} = \text{trans.returned\_at}$ (UTC timestamp on return request).
   - If $T_{\text{return}} \le T_{\text{due}}$: On-time $\implies \text{borrower.karma} \mathrel{+}= 5$.
   - If $T_{\text{return}} > T_{\text{due}}$: Late $\implies \text{borrower.karma} \mathrel{-}= 30$.
   - Owner always gets: $\text{owner.karma} \mathrel{+}= 10$.
3. **Schema and UI Updates**:
   - `models.User.karma = Column(Integer, default=100)`.
   - `schemas.UserOut.karma: int = 100`. Keep `trust_score` property for backward compatibility.
   - Frontend `Profile.jsx`, `ItemDetail.jsx`, `ItemCard.jsx` display "Karma: 100" instead of generic "⭐ 4.5".

### 2.4 Logic: Automated Evaluation Loop & 20-Point Judge Rubric (R5)
1. **Observation**: R5 requires an Agent-as-Judge evaluator assessing the integrated system against a 20-point rubric across 5 categories (4 pts each), passing if score $\ge 18/20$.
2. **Rubric Architecture**:
   - **Section 1: Architecture Integration & Cleanup (4 pts)**:
     - 1.1: `Tanvir/` folder completely deleted (1 pt).
     - 1.2: `/api/landmarks` endpoint returns valid 700m radius campus metadata & zones (1 pt).
     - 1.3: Active seed items from `kuet_landmarks.json` accessible via `/api/items` (1 pt).
     - 1.4: MapLibre GL and Turf.js integrated into React `frontend/` (1 pt).
   - **Section 2: UI Layout & Modern Dashboard (4 pts)**:
     - 2.1: Left sidebar navigation with Map View, My Items, Requests, Profile (1 pt).
     - 2.2: Top bar with search/filter and "Add Item" modal trigger (1 pt).
     - 2.3: MapLibre map rendered in main content area with campus perimeter ring (1 pt).
     - 2.4: Hover cards / popups displaying item specs and mini-map locations (1 pt).
   - **Section 3: Authentication & KUET Roll Decoder (4 pts)**:
     - 3.1: Non-KUET emails rejected with HTTP 400 (1 pt).
     - 3.2: Automated parsing of Batch (`25`), Dept (`07`), and Roll (`028`) from `siddique52507028@stud.kuet.ac.bd` (1 pt).
     - 3.3: Registration only requires Name, Email, and Password (1 pt).
     - 3.4: Password hashed with bcrypt and JWT access token issued upon login (1 pt).
   - **Section 4: KUET Karma Protocol (4 pts)**:
     - 4.1: New users start with 100 Base Karma (1 pt).
     - 4.2: Successful transaction awards +10 Karma to the owner/lender (1 pt).
     - 4.3: On-time return awards +5 Karma to the borrower (1 pt).
     - 4.4: Late return deducts -30 Karma from the borrower (1 pt).
   - **Section 5: End-to-End User Experience (4 pts)**:
     - 5.1: Item creation with pinpointed coordinates succeeds (1 pt).
     - 5.2: Borrow request creation succeeds and prevents duplicate requests (1 pt).
     - 5.3: Request acceptance auto-declines conflicting requests for the same item (1 pt).
     - 5.4: Full Handover (OTP/QR) and Return flow completes without error (1 pt).
3. **Execution**: A standalone Python script `judge_rubric.py` at the project root can run all tests against the backend API and frontend bundle, printing a structured breakdown and exit code.

---

## 3. Caveats
- **Area Not Investigated**: Real WebSocket server for live chat. `backend/app/routes/chat.py` implements REST-based polling for messages; this is sufficient for the MVP and problem statement.
- **Node.js Environment**: `node` and `npm` were not found in the immediate environment PATH. Frontend build verification should use available local paths or run in an environment with Node.js configured.
- **Roll Storage Convention**: `ORIGINAL_REQUEST.md` specifically notes `Batch=25, Dept=07, Roll=028`. Some KUET systems format batch as `2025` and roll as `2507028`. The backend implementation should accommodate both formats (e.g., storing `batch="25"`, `dept="07"`, `roll="028"` while providing `full_roll="2507028"`).
- **SQLite Concurrency**: SQLite with WAL mode (`PRAGMA journal_mode=WAL;`) should be enabled if concurrent judge requests run in parallel.

---

## 4. Conclusion & Actionable Blueprint

### Required Backend Changes
1. **`backend/app/models.py`**:
   - `User`: Add `karma = Column(Integer, default=100)`. Keep `trust_score` property for compatibility. Update default `trust_score` to `100.0`. Ensure `roll` uniqueness accommodates department partitioning or composite key `UniqueConstraint('batch', 'dept', 'roll')`.
   - `Item`: Add `type = Column(String, default="lend")` (supports `"lend"` and `"borrow"` beacons), `specs = Column(Text, nullable=True)`, and `tags = Column(Text, nullable=True)`.
2. **`backend/app/schemas.py`**:
   - `UserRegister`: Accept only `name`, `email`, `password`.
   - `UserOut`: Include `karma: int = 100`.
   - `ItemBase` / `ItemOut`: Add `type: Optional[str] = "lend"`, `specs: Optional[str] = None`, `tags: Optional[List[str]] = None`, `lat`/`lng` field aliases.
   - `TransactionOut`: Add `TransactionOut` schema with `id`, `request_id`, `otp`, `qr_code`, `status`, `borrowed_at`, `returned_at`.
   - `BorrowRequestOut`: Add `transaction: Optional[TransactionOut] = None` to resolve Bug 1.
3. **`backend/app/routes/auth.py`**:
   - Implement `parse_kuet_email(email)` enforcing `@stud.kuet.ac.bd` and regex `(\d{2})(\d{2})(\d{3})$`.
   - Automatically populate `batch`, `dept`, `roll` on registration.
   - Add alias `GET /api/auth/current` pointing to `get_current_user_info` for compatibility with `Tanvir/` legacy contracts.
4. **`backend/app/routes/items.py`**:
   - Update `list_items` to filter by `category`, `type` (`lend` vs `borrow`), and search query.
   - Update `create_item` to support both JSON body (`schemas.ItemCreate`) and `multipart/form-data`.
5. **`backend/app/routes/borrow_requests.py`**:
   - In `update_request_status`: Accept `status` from either JSON body (`BorrowRequestStatusUpdate`) or query parameter (`status: Optional[str] = None`) to resolve Bug 2.
6. **`backend/app/routes/transactions.py`**:
   - Implement Karma calculation in `request_return`:
     - `owner.karma = (owner.karma or 100) + 10`
     - Compare `trans.returned_at` with `trans.borrowed_at + timedelta(hours=req.duration_hours)`
     - On-time: `borrower.karma = (borrower.karma or 100) + 5`
     - Late: `borrower.karma = (borrower.karma or 100) - 30`
7. **`backend/app/routes/landmarks.py`**:
   - Create router serving `GET /api/landmarks` from `kuet_landmarks.json`.
8. **Database Seeding (`backend/app/seed.py`)**:
   - Automatically seed 21 landmarks, 8 student users (with 100 base karma), and 10 active items (7 lend, 3 borrow beacons).
9. **Cleanup**:
   - Remove orphaned `backend/app/routes/requests.py`.

---

## 5. Verification Method

### 5.1 Verification Commands
1. **Verification of Email Roll Decoder & Karma Protocol via Unit Script**:
   ```bash
   python3 -c "
   import re
   def decode_kuet_email(email):
       assert email.endswith('@stud.kuet.ac.bd'), 'Must end with @stud.kuet.ac.bd'
       prefix = email.split('@')[0]
       m = re.search(r'(\d{2})(\d{2})(\d{3})$', prefix)
       assert m, 'Cannot parse roll digits'
       return {'batch': m.group(1), 'dept': m.group(2), 'roll': m.group(3)}

   res = decode_kuet_email('siddique52507028@stud.kuet.ac.bd')
   assert res['batch'] == '25', f'Expected 25, got {res[\"batch\"]}'
   assert res['dept'] == '07', f'Expected 07, got {res[\"dept\"]}'
   assert res['roll'] == '028', f'Expected 028, got {res[\"roll\"]}'
   print('[PASS] Roll Decoder Test Passed:', res)
   "
   ```

2. **Verification of End-to-End API Flow with Standalone Test Client**:
   A comprehensive test script `verify_backend_e2e.py` testing:
   - Registration with non-KUET email (expects 400)
   - Registration with `siddique52507028@stud.kuet.ac.bd` (expects Batch 25, Dept 07, Roll 028, Karma 100)
   - Login and JWT bearer token issuance
   - Item listing and landmark fetching
   - Item creation (lend item)
   - Borrow request creation
   - Request acceptance by owner
   - Handover start (OTP generation) and verification
   - Return confirmation with on-time (+5 / +10) and late (-30 / +10) Karma assertions

3. **Verification of 20-Point Problem Statement Rubric**:
   Run the Judge Evaluator script:
   ```bash
   python3 judge_rubric.py
   ```
   **Pass Condition**: Total Score $\ge 18 / 20$.
   **Invalidation Conditions**:
   - If any non-KUET email registers successfully.
   - If user karma starts at generic 4.5/5.0 instead of 100.
   - If late return does not deduct 30 karma points.
   - If `Tanvir/` folder remains in repository root.
   - If borrow request return cannot be completed due to missing schema fields.
