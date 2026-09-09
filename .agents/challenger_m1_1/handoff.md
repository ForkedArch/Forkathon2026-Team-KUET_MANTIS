# Adversarial Challenge Report: Milestone 1 Auth & Items APIs

**Agent**: `challenger_m1_1`  
**Role**: Empirical Challenger / Critic / Specialist  
**Working Directory**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/challenger_m1_1`  
**Target File**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/challenger_m1_1/handoff.md`  
**Date**: 2026-09-10  
**Explicit Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

Direct observations from writing and executing the automated adversarial stress harness (`backend/test_adversarial_challenger.py` — 61 tests across 6 suites):

### 1.1 Unhandled `IntegrityError` (HTTP 500) on Concurrent Registrations
- **File**: `backend/app/routes/auth.py:28-63`
- **Command Executed**:
  ```bash
  python3 backend/test_adversarial_challenger.py
  ```
- **Observed Result**:
  - In Suite 5.1 (5 concurrent requests attempting registration with the same fresh email `race_exact_...@stud.kuet.ac.bd`):
    - Responses: `[500, 500, 500, 200, 500]` (1 succeeded with 200, 4 failed with 500).
    - Verbatim Exception:
      ```
      sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) UNIQUE constraint failed: users.email
      [SQL: INSERT INTO users (email, name, dept, batch, roll, hashed_password, is_verified, karma, trust_score, total_lends, total_borrows, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)]
      ```
  - In Suite 5.2 (3 concurrent requests with different emails decoding to the same batch, dept, and roll `46-07-918`):
    - Responses: `[500, 200, 500]` (1 succeeded with 200, 2 failed with 500).
    - Verbatim Exception:
      ```
      sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) UNIQUE constraint failed: users.batch, users.dept, users.roll
      [SQL: INSERT INTO users (email, name, dept, batch, roll, hashed_password, is_verified, karma, trust_score, total_lends, total_borrows, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)]
      ```
  - **Location in Code**:
    In `backend/app/routes/auth.py:59-61`:
    ```python
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    ```
    There is no `try ... except IntegrityError:` handler around `db.commit()`. When concurrent threads pass the initial `filter().first()` check before commits happen, the second thread crashes the ASGI worker with an uncaught 500 error instead of a clean 400/409 HTTP response.

### 1.2 Whitespace-Only Titles Accepted in Item Creation
- **File**: `backend/app/routes/items.py:116`
- **Observed Result**:
  - Request: `POST /api/items/` with JSON payload `{"title": "   ", "type": "lend"}`.
  - Response: `HTTP 201 Created`
  - Verbatim Output:
    `{"success": true, "item": {"title": "   ", "category": "Other", "type": "lend", "status": "available", "is_available": true, ...}}`
  - **Location in Code**:
    `backend/app/routes/items.py:116`:
    ```python
    if not title:
        raise HTTPException(status_code=422, detail="Title is required")
    ```
    In Python, `bool("   ")` is `True`, so `not title` evaluates to `False`. The check fails to strip whitespace, permitting empty title cards and blank map pins.

### 1.3 Invalid Item Type Accepted (`type="destroy"`)
- **File**: `backend/app/routes/items.py:71, 87` & `backend/app/schemas.py:68`
- **Observed Result**:
  - Request: `POST /api/items/` with JSON payload `{"title": "Invalid Type Test", "type": "destroy"}`.
  - Response: `HTTP 201 Created`
  - Stored item has `type="destroy"`. Per `PROJECT.md` Feature 15 and `MapItemPin` contract, `type` must strictly be `"lend" | "borrow"`. Arbitrary strings bypass schema validation and pollute map marker rendering.

### 1.4 Unauthenticated Item Creation Allows Student Roll Spoofing
- **File**: `backend/app/routes/items.py:118-128`
- **Observed Result**:
  - Request: `POST /api/items/` without any `Authorization` header, payload: `{"title": "Anonymous Spoofed Item", "type": "lend", "roll": "010"}`.
  - Response: `HTTP 201 Created`
  - Verbatim Response:
    `Attributed to: Siddique Ahmed (roll: 010, karma: 100)`
  - **Location in Code**:
    ```python
    owner = current_user
    if not owner and owner_id:
        owner = db.query(models.User).filter(models.User.id == int(owner_id)).first()
    if not owner and roll:
        owner = db.query(models.User).filter(models.User.roll == str(roll)).first()
    if not owner:
        owner = db.query(models.User).first()
    ```
    Any unauthenticated client can impersonate arbitrary students by passing their roll, or by omitting auth entirely (falling back to `db.query(models.User).first()`).

### 1.5 Empty Password & Whitespace Name Registrations Accepted
- **File**: `backend/app/schemas.py:13-16` & `backend/app/routes/auth.py:51`
- **Observed Result**:
  - `POST /api/auth/register` with `{"name": "Valid Student", "email": "...@stud.kuet.ac.bd", "password": ""}` returned `HTTP 200 OK`.
  - The user was successfully created with a bcrypt hash of `""` and was subsequently able to log in with `password=""` to receive a JWT bearer token.
  - `POST /api/auth/register` with `{"name": "   ", ...}` returned `HTTP 200 OK` and stored `name=""`.

### 1.6 Unicode Digit Spoofing of Student Roll
- **File**: `backend/app/routes/auth.py:18`
- **Observed Result**:
  - Registration with Bengali digits: `tanvir২৫০৭...` returned `HTTP 200 OK`.
  - Decoder extracted: `batch="২৫", dept="০৭", roll="..."`.
  - Because `re.search(r'(\d{2})(\d{2})(\d{3})$', local_part)` lacks `re.ASCII`, Python 3 `\d` matches all Unicode decimal digit category (`Nd`) characters. This creates duplicate pseudo-accounts that visual collision checks miss.

### 1.7 Areas Handled Robustly (Zero Bugs Found)
- **Email Domain Checks**: 18 adversarial test cases tested (evil domain suffixes like `.evil.com`, subdomain prefixes, non-KUET domains, missing digits, non-numeric suffixes). All 18 rejected with HTTP 400 or HTTP 422.
- **SQL Injection**: 13 adversarial SQLi vectors injected across `/api/auth/register` fields (`name`, `password`, `email`), `/api/items` search queries (`q`), category filters, and item creation payloads. All handled securely via ORM parameterized queries with zero 500 errors.
- **Boundary Student Rolls**: Minimum (`00-00-000`), maximum (`99-99-999`), and zero-leading rolls (`001`, `010`) accurately preserved leading zeroes as strings.
- **Item Authorization**: Unauthorized item edits (`PUT`) and deletes (`DELETE`) rejected with HTTP 403 Forbidden. Non-existent items return HTTP 404.
- **Borrow Request Integrity**: Requesting own item rejected with HTTP 400. Duplicate pending requests rejected with HTTP 400.

---

## 2. Logic Chain

1. **Premise 1 (Observation 1.1)**: Under concurrent registrations, bcrypt password hashing takes ~100ms. Multiple concurrent requests pass `db.query(models.User).filter(...).first()` simultaneously. When the first commits, subsequent commits trigger SQLite unique constraints (`users.email` and `users.batch, users.dept, users.roll`).
2. **Premise 2 (Observation 1.1)**: In `backend/app/routes/auth.py`, `db.commit()` is not enclosed in a `try...except IntegrityError`. The unhandled `IntegrityError` bubbles up to the ASGI server, emitting an HTTP 500 Internal Server Error.
3. **Inference 1**: Under real campus registration surges (e.g. fresh batch orientation), students attempting to register duplicate emails or colliding rolls will cause server crashes (500) rather than deterministic client rejections (400/409).
4. **Premise 3 (Observations 1.2 & 1.3)**: `POST /api/items/` accepts whitespace-only titles (`title="   "`) and invalid types (`type="destroy"`).
5. **Inference 2**: In Milestone 2, the frontend renders map markers and hover cards based on item title and type (`lend` vs `borrow`). Whitespace titles produce blank cards, and unexpected types break marker clustering and radar pulse logic.
6. **Premise 4 (Observation 1.5)**: Registration allows empty passwords and whitespace names, allowing unauthenticated or bot accounts to flood the database with zero-character credentials.
7. **Conclusion**: While core functional requirements (R1, R3, R4) operate as claimed in single-threaded tests, the system is brittle under multi-user concurrency and lacks basic defensive validation. Therefore, Milestone 1 cannot be approved without fixing these defects.

---

## 3. Caveats

- **Load Testing Threshold**: Concurrency was tested with 5 concurrent threads using Python's `ThreadPoolExecutor` and SQLite with `check_same_thread=False`. In a multi-worker Uvicorn deployment or under PostgreSQL, the same underlying `IntegrityError` will occur without proper exception handling.
- **Demo Mode Fallback**: The unauthenticated item creation fallback (`owner = db.query(models.User).first()`) in `items.py:125` may have been added intentionally for demo/seed compatibility. However, in an adversarial review, it constitutes an authentication bypass.

---

## 4. Conclusion

**Verdict: REQUEST_CHANGES**

Milestone 1 backend implementation is functional for basic happy-paths, but fails adversarial stress testing due to an unhandled 500 error on concurrent registrations, input validation bypasses, and credential sanitization issues.

### Required Changes for Worker M1:
1. **Fix Concurrency Crash in `backend/app/routes/auth.py`**:
   Wrap `db.commit()` in `try ... except IntegrityError`:
   ```python
   from sqlalchemy.exc import IntegrityError
   ...
   try:
       db.add(new_user)
       db.commit()
       db.refresh(new_user)
   except IntegrityError:
       db.rollback()
       raise HTTPException(
           status_code=400,
           detail="Email or roll number already registered for this batch and department"
       )
   ```
2. **Fix Item Title & Type Validation in `backend/app/routes/items.py`**:
   - Check non-empty title:
     ```python
     if not title or not str(title).strip():
         raise HTTPException(status_code=422, detail="Title is required and cannot be empty")
     ```
   - Restrict type to `{"lend", "borrow"}`:
     ```python
     if item_type not in ("lend", "borrow"):
         raise HTTPException(status_code=422, detail="Item type must be 'lend' or 'borrow'")
     ```
3. **Enforce Minimum Credential Lengths in `backend/app/schemas.py`**:
   - Update `UserRegister`:
     ```python
     from pydantic import Field
     class UserRegister(BaseModel):
         name: str = Field(..., min_length=2)
         email: EmailStr
         password: str = Field(..., min_length=4)
     ```
4. **Enforce ASCII Digits in Roll Decoder (`auth.py:18`)**:
   Use `re.ASCII` flag:
   ```python
   match = re.search(r'(\d{2})(\d{2})(\d{3})$', local_part, re.ASCII)
   ```

---

## 5. Verification Method

To independently verify these findings:

1. **Run the Automated Adversarial Challenger Suite**:
   ```bash
   python3 backend/test_adversarial_challenger.py
   ```
   *Expected Output*:
   - 61 total tests executed.
   - Empirical confirmation of the 500 concurrency errors, whitespace title acceptance, and empty password acceptance.

2. **Run the Concurrency Race Condition Reproduction Script**:
   ```bash
   python3 -c "
   import sys, random, concurrent.futures
   sys.path.insert(0, 'backend')
   from app.main import app
   from test_adversarial_challenger import RobustASGIClient
   client = RobustASGIClient(app)
   roll = random.randint(500, 899)
   em1 = f'race_a_9101{roll}@stud.kuet.ac.bd'
   em2 = f'race_b_9101{roll}@stud.kuet.ac.bd'
   with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
       f1 = ex.submit(client.post, '/api/auth/register', json={'name':'R1','email':em1,'password':'p1'})
       f2 = ex.submit(client.post, '/api/auth/register', json={'name':'R2','email':em2,'password':'p2'})
       print('Status 1:', f1.result().status_code, 'Status 2:', f2.result().status_code)
   "
   ```
   *Expected Result*: Status `500` is returned on one of the colliding requests due to unhandled `IntegrityError`.

3. **Invalidation Conditions**:
   - The changes can be approved once `python3 backend/test_adversarial_challenger.py` exits with `FAILED (BUGS): 0` and concurrent registrations cleanly return HTTP 400 instead of HTTP 500.
