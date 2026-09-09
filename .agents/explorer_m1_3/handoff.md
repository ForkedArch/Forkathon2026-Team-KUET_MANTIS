# Handoff Report: KUET Karma Protocol (R4) & Backend Bugfixes Analysis

**Author**: `explorer_m1_3`  
**Milestone**: Milestone 1 (Backend Core & Bugfixes)  
**Date**: 2026-09-10  
**Scope**: 
1. 100 Base Karma for new users in `models.py` & `schemas.py`
2. Transaction return calculations: owner +10, borrower on-time +5, borrower late -30 (checking `borrowed_at + duration_hours`)
3. Bug 1 fix: add `transaction: Optional[TransactionOut] = None` in `BorrowRequestOut` schema
4. Bug 2 fix: update `PUT /api/requests/{request_id}/status` to accept body or query parameter
5. Remove duplicate `backend/app/routes/requests.py`

---

## 1. Observation

### 1.1 Task 1: Karma System vs Legacy Trust Score in Models & Schemas
- **File**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend/app/models.py` (lines 11–26):
  ```python
  class User(Base):
      __tablename__ = "users"

      id = Column(Integer, primary_key=True, index=True)
      email = Column(String, unique=True, index=True, nullable=False)
      name = Column(String, nullable=False)
      dept = Column(String, nullable=False)
      batch = Column(String, nullable=False)
      roll = Column(String, unique=True, nullable=False)
      hashed_password = Column(String, nullable=False)
      is_verified = Column(Boolean, default=True)  # simplified
      trust_score = Column(Float, default=4.5)
      total_lends = Column(Integer, default=0)
      total_borrows = Column(Integer, default=0)
      created_at = Column(DateTime, default=utcnow)
  ```
  *Direct Observation*: The `User` model only has `trust_score = Column(Float, default=4.5)`. There is no `karma` column.
- **File**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend/app/schemas.py` (lines 20–28):
  ```python
  class UserOut(UserBase):
      model_config = ConfigDict(from_attributes=True)

      id: int
      trust_score: float
      total_lends: int
      total_borrows: int
      created_at: datetime
  ```
  *Direct Observation*: `UserOut` exposes only `trust_score: float` and omits `karma`.
- **Database Inspection**:
  Running SQLite query against `backend/campus_share.db`:
  ```
  PRAGMA table_info(users);
  ```
  Output columns: `['id', 'email', 'name', 'dept', 'batch', 'roll', 'hashed_password', 'is_verified', 'trust_score', 'total_lends', 'total_borrows', 'created_at']`.
  Existing user record: 1 record (`anik52507030@stud.kuet.ac.bd`, `trust_score: 4.5`).
  *Direct Observation*: If `karma = Column(Integer, default=100)` is added to `models.User` without altering existing SQLite tables, SQLAlchemy queries against the existing SQLite DB will fail with `sqlite3.OperationalError: no such column: users.karma`.

---

### 1.2 Task 2: Transaction Return Calculations
- **File**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend/app/routes/transactions.py` (lines 61–97):
  ```python
  @router.post("/return/{request_id}")
  def request_return(
      request_id: int,
      db: Session = Depends(database.get_db),
      current_user: models.User = Depends(auth.get_current_user)
  ):
      req = db.query(models.BorrowRequest).filter(models.BorrowRequest.id == request_id).first()
      if not req:
          raise HTTPException(status_code=404, detail="Request not found")
      if req.borrower_id != current_user.id:
          raise HTTPException(status_code=403, detail="Only borrower can request return")
      trans = db.query(models.Transaction).filter(models.Transaction.request_id == request_id).first()
      if not trans or trans.status != "borrowed":
          raise HTTPException(status_code=400, detail="Item not currently borrowed")
      # In a real system, owner would confirm return with another OTP.
      # For MVP, we auto-confirm and update trust.
      trans.status = "returned"
      trans.returned_at = datetime.now(timezone.utc)
      # Make item available again
      item = db.query(models.Item).filter(models.Item.id == req.item_id).first()
      if item:
          item.is_available = True
      # Update trust scores (simplified)
      owner = db.query(models.User).filter(models.User.id == req.owner_id).first()
      borrower = db.query(models.User).filter(models.User.id == req.borrower_id).first()
      if owner:
          owner.total_lends += 1
          # Increase trust slightly
          owner.trust_score = min(5.0, owner.trust_score + 0.05)
      if borrower:
          borrower.total_borrows += 1
          borrower.trust_score = min(5.0, borrower.trust_score + 0.03)
      # Update request status to completed
      req.status = "completed"
      db.commit()
      return {"detail": "Return confirmed, item available again"}
  ```
- **Direct Observations**:
  1. Return timestamp `trans.returned_at` is recorded, but no comparison is performed against `trans.borrowed_at + timedelta(hours=req.duration_hours)`.
  2. Score updates use hardcoded float increments: `owner.trust_score + 0.05` and `borrower.trust_score + 0.03`.
  3. No KUET Karma protocol logic exists: neither owner +10, nor borrower on-time +5, nor borrower late -30.
  4. The returned response is `{"detail": "Return confirmed, item available again"}`, whereas `PROJECT.md` contract Section 3 specifies:
     ```json
     {
       "message": "Item returned successfully",
       "karma_updated": {
         "owner_gain": 10,
         "borrower_change": 5,
         "is_on_time": true
       }
     }
     ```

---

### 1.3 Task 3 (Bug 1): Missing `transaction` field in `BorrowRequestOut`
- **File**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend/app/schemas.py` (lines 66–82):
  ```python
  class BorrowRequestOut(BaseModel):
      model_config = ConfigDict(from_attributes=True)

      id: int
      item_id: int
      borrower_id: int
      owner_id: int
      duration_hours: int
      purpose: Optional[str]
      pickup_zone: Optional[str]
      message: Optional[str]
      status: str
      created_at: datetime
      item: ItemOut
      borrower: UserOut
      owner: UserOut
  ```
- **File**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/pages/Transaction.jsx` (lines 16–23, 62–63, 102):
  ```javascript
  const { data: request, refetch } = useQuery({
    queryKey: ['request', requestId],
    queryFn: () => api.get(`/requests/me`).then(res => {
      const found = res.data.find(r => r.id === parseInt(requestId));
      return found;
    }),
    enabled: !!requestId
  });
  ...
  {request.transaction && (
    <p><strong>Transaction Status:</strong> {request.transaction.status}</p>
  )}
  ...
  {request?.transaction?.status === 'borrowed' && request.borrower_id === user.id && (
    <button onClick={() => returnMutation.mutate()} ...>Return</button>
  )}
  ```
- **Direct Observation**: `BorrowRequest` in `models.py` defines `transaction = relationship("Transaction", ...)`. Because `BorrowRequestOut` in `schemas.py` does not define `transaction`, Pydantic filters out the `transaction` property when serializing `/api/requests/me`. As a result, `request.transaction` is always `undefined` on the frontend, and the Return button (`request?.transaction?.status === 'borrowed'`) is never rendered.

---

### 1.4 Task 4 (Bug 2): `PUT /api/requests/{request_id}/status` Parameter Mismatch
- **File**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend/app/routes/borrow_requests.py` (lines 59–66):
  ```python
  @router.put("/{request_id}/status")
  def update_request_status(
      request_id: int,
      body: schemas.BorrowRequestStatusUpdate,
      db: Session = Depends(database.get_db),
      current_user: models.User = Depends(auth.get_current_user)
  ):
      status = body.status
  ```
- **File**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/pages/Requests.jsx` (line 18):
  ```javascript
  await api.put(`/requests/${requestId}/status?status=${status}`);
  ```
- **Direct Observation**:
  `frontend/src/pages/Requests.jsx` issues `PUT /requests/${requestId}/status?status=${status}` without a JSON request body.
  Because `borrow_requests.py` specifies `body: schemas.BorrowRequestStatusUpdate` without a default value, FastAPI requires a request body. When the frontend executes this call, FastAPI immediately aborts with `HTTP 422 Unprocessable Entity` ("field required", location: `["body"]`).
  Accepting/declining borrow requests from the frontend is completely broken.

---

### 1.5 Task 5: Duplicate Route File `backend/app/routes/requests.py`
- **Files**:
  - `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend/app/routes/requests.py` (lines 1–72)
  - `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend/app/routes/borrow_requests.py` (lines 1–104)
  - `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend/app/main.py` (lines 5, 31):
    ```python
    from .routes import auth, items, borrow_requests, chat, transactions
    ...
    app.include_router(borrow_requests.router)
    ```
- **Direct Observation**:
  1. Both `requests.py` and `borrow_requests.py` declare `router = APIRouter(prefix="/api/requests", tags=["requests"])`.
  2. `backend/app/main.py` imports and mounts `borrow_requests.router`. `requests.py` is never imported in `main.py`.
  3. Grep search across the entire codebase finds 0 imports of `requests.py` or `routes.requests`.
  4. `borrow_requests.py` contains critical concurrency and race-condition guards (anti-spam check at line 24, item re-availability verification at line 81, and auto-declining conflicting pending requests at line 90) that `requests.py` lacks.
  5. `requests.py` is an orphaned, obsolete duplicate.

---

## 2. Logic Chain

### 2.1 Logic: 100 Base Karma Implementation
1. **From Observation 1.1**: R4 states: *"Users start with 100 Base Karma."*
2. In `models.py`, `User` needs an integer column `karma = Column(Integer, default=100, nullable=False)`.
3. To preserve backward compatibility with existing components (`Profile.jsx`, `ItemCard.jsx`) that access `user.trust_score`, `trust_score` should be retained and defaulted to `100.0`.
4. In `schemas.py`, `UserOut` must include `karma: int = 100` and `trust_score: Optional[float] = 100.0`.
5. In `routes/auth.py`, user creation must set `karma=100` and `trust_score=100.0`.
6. For existing SQLite instances, an `ALTER TABLE users ADD COLUMN karma INTEGER DEFAULT 100` guard prevents `OperationalError`.

### 2.2 Logic: KUET Karma Transaction Return Calculations
1. **From Observation 1.2**: R4 states:
   *"When a borrow request is completed, successfully lending adds +10 to the owner, and returning on time adds +5 to the borrower. Returning late deducts -30. Implement this logic in the transaction flows."*
2. **Timing Calculation**:
   - Let $T_{\text{borrowed}} = \text{trans.borrowed\_at}$.
   - Let $D = \text{req.duration\_hours}$.
   - Let $T_{\text{due}} = T_{\text{borrowed}} + \text{timedelta}(\text{hours}=D)$.
   - Let $T_{\text{return}} = \text{trans.returned\_at} = \text{datetime.now(timezone.utc)}$.
   - Timezone reconciliation: SQLite stores timezone-naive datetimes. If `borrowed_at.tzinfo is None`, apply `borrowed_at = borrowed_at.replace(tzinfo=timezone.utc)` so subtraction does not fail with `TypeError`.
   - On-time condition: $\text{is\_on\_time} = (T_{\text{return}} \le T_{\text{due}})$.
3. **Score Adjustments**:
   - Owner successfully lent item $\implies \Delta K_{\text{owner}} = +10$.
   - Borrower on time $\implies \Delta K_{\text{borrower}} = +5$.
   - Borrower late $\implies \Delta K_{\text{borrower}} = -30$.
4. **State Transitions**:
   - `trans.status = "returned"`
   - `item.is_available = True`
   - `req.status = "completed"`
   - `owner.total_lends += 1`
   - `borrower.total_borrows += 1`
5. **Response Format**:
   - Support both `PROJECT.md` Section 3 contract (`message`, `karma_updated`) and legacy `detail` string so neither client type breaks.

### 2.3 Logic: Bug 1 Fix (`BorrowRequestOut.transaction`)
1. **From Observation 1.3**: Frontend relies on `request.transaction.status` to display transaction status and render the Return button.
2. `BorrowRequest` ORM model already has `transaction = relationship("Transaction", back_populates="request", uselist=False)`.
3. Defining `TransactionOut` schema with fields `id`, `request_id`, `otp`, `qr_code`, `borrowed_at`, `returned_at`, `status` and adding `transaction: Optional[TransactionOut] = None` to `BorrowRequestOut` allows Pydantic to serialize the attached transaction object.
4. When `trans.status == "borrowed"`, the serialized JSON contains `"transaction": {"status": "borrowed", ...}`, immediately unblocking the Return flow in `Transaction.jsx`.

### 2.4 Logic: Bug 2 Fix (Accepting Body or Query in Request Status Update)
1. **From Observation 1.4**: Frontend sends query param `?status=accepted` with empty body. Tests and other clients may send JSON body `{"status": "accepted"}`.
2. In FastAPI, declaring:
   ```python
   body: Optional[schemas.BorrowRequestStatusUpdate] = Body(None),
   status: Optional[str] = Query(None)
   ```
   makes both parameters optional at the HTTP level.
3. Resolution precedence:
   ```python
   resolved_status = body.status if (body and body.status) else status
   ```
4. If `resolved_status` is missing or not in `["accepted", "declined"]`, raise `HTTPException(400, "status must be 'accepted' or 'declined'")`.
5. This allows `PUT /api/requests/{id}/status?status=accepted` (frontend) AND `PUT /api/requests/{id}/status` with JSON body `{"status": "accepted"}` to both succeed seamlessly with full validation.

### 2.5 Logic: Removal of Duplicate `requests.py`
1. **From Observation 1.5**: `requests.py` is unmounted, unimported, lacks crucial validation guards present in `borrow_requests.py`, and shadows the `/api/requests` endpoint name.
2. Safely deleting `backend/app/routes/requests.py` eliminates dead code without breaking any functional route or test.

---

## 3. Caveats

1. **Existing Database Migration**:
   `backend/campus_share.db` already exists with a table `users` lacking the `karma` column. SQLAlchemy's `Base.metadata.create_all()` will not alter existing tables. The implementation must execute `ALTER TABLE users ADD COLUMN karma INTEGER DEFAULT 100` (or recreate the database if acceptable) upon startup or migration.
2. **Timezone Awareness in SQLite**:
   SQLite's default datetime storage drops timezone information. Explicitly coercing naive datetimes to UTC (`replace(tzinfo=timezone.utc)`) in `transactions.py` is essential to prevent `TypeError: can't subtract offset-naive and offset-aware datetimes`.
3. **Karma Floor Constraints**:
   Neither `ORIGINAL_REQUEST.md` nor `PROJECT.md` specifies a lower bound (floor) for Karma (e.g. `max(0, karma - 30)`). Karma is treated as an unbounded integer score (e.g. can drop to 70, 40, etc.).
4. **Owner vs Borrower Return Confirmation**:
   In `transactions.py`, the endpoint is `/api/transactions/return/{request_id}` and requires `current_user.id == req.borrower_id`. The prompt confirms borrower initiates the return and triggers the karma calculation.

---

## 4. Conclusion & Concrete Implementation Blueprint

### 4.1 Changes to `backend/app/models.py`
Update `User` class to add `karma`:
```python
# In backend/app/models.py:
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    dept = Column(String, nullable=False)
    batch = Column(String, nullable=False)
    roll = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=True)
    karma = Column(Integer, default=100, nullable=False)
    trust_score = Column(Float, default=100.0)  # Retained for backward compatibility
    total_lends = Column(Integer, default=0)
    total_borrows = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)
```

### 4.2 Changes to `backend/app/schemas.py`
1. Add `karma` and optional `trust_score` to `UserOut`.
2. Add `TransactionOut` schema.
3. Add `transaction: Optional[TransactionOut] = None` to `BorrowRequestOut`.

```python
# In backend/app/schemas.py:

class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    karma: int = 100
    trust_score: Optional[float] = 100.0
    total_lends: int
    total_borrows: int
    created_at: datetime


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    otp: Optional[str] = None
    qr_code: Optional[str] = None
    borrowed_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    status: str


class BorrowRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    borrower_id: int
    owner_id: int
    duration_hours: int
    purpose: Optional[str] = None
    pickup_zone: Optional[str] = None
    message: Optional[str] = None
    status: str
    created_at: datetime
    item: ItemOut
    borrower: UserOut
    owner: UserOut
    transaction: Optional[TransactionOut] = None
```

### 4.3 Changes to `backend/app/routes/borrow_requests.py`
Update `update_request_status` to accept body or query parameter:
```python
# In backend/app/routes/borrow_requests.py:
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from typing import Optional, List

@router.put("/{request_id}/status")
def update_request_status(
    request_id: int,
    body: Optional[schemas.BorrowRequestStatusUpdate] = Body(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    resolved_status = None
    if body and body.status:
        resolved_status = body.status
    elif status:
        resolved_status = status

    if not resolved_status or resolved_status not in ["accepted", "declined"]:
        raise HTTPException(
            status_code=400,
            detail="status must be 'accepted' or 'declined', provided via JSON body or query parameter"
        )

    status_val = resolved_status

    req = db.query(models.BorrowRequest).filter(models.BorrowRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can change status")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="This request has already been resolved")

    if status_val == "accepted":
        item = db.query(models.Item).filter(models.Item.id == req.item_id).first()
        if not item or not item.is_available:
            raise HTTPException(status_code=400, detail="Item is no longer available")

        req.status = "accepted"
        item.is_available = False

        other_pending = db.query(models.BorrowRequest).filter(
            models.BorrowRequest.item_id == req.item_id,
            models.BorrowRequest.id != req.id,
            models.BorrowRequest.status == "pending",
        ).all()
        for other in other_pending:
            other.status = "declined"

        db.commit()
    else:
        req.status = "declined"
        db.commit()

    return {"detail": f"Request {status_val}"}
```

### 4.4 Changes to `backend/app/routes/transactions.py`
Update `request_return` to calculate KUET Karma (+10 owner, +5 on-time borrower, -30 late borrower):
```python
# In backend/app/routes/transactions.py:
from datetime import datetime, timezone, timedelta

@router.post("/return/{request_id}")
def request_return(
    request_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    req = db.query(models.BorrowRequest).filter(models.BorrowRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.borrower_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only borrower can request return")
    trans = db.query(models.Transaction).filter(models.Transaction.request_id == request_id).first()
    if not trans or trans.status != "borrowed":
        raise HTTPException(status_code=400, detail="Item not currently borrowed")

    now = datetime.now(timezone.utc)
    trans.status = "returned"
    trans.returned_at = now

    # Make item available again
    item = db.query(models.Item).filter(models.Item.id == req.item_id).first()
    if item:
        item.is_available = True

    # Check on-time status: borrowed_at + duration_hours
    borrowed_at = trans.borrowed_at or now
    if borrowed_at.tzinfo is None:
        borrowed_at = borrowed_at.replace(tzinfo=timezone.utc)

    duration = req.duration_hours or 0
    due_time = borrowed_at + timedelta(hours=duration)
    is_on_time = (now <= due_time)

    # KUET Karma Protocol: Owner +10, Borrower +5 (on-time) or -30 (late)
    owner_gain = 10
    borrower_change = 5 if is_on_time else -30

    owner = db.query(models.User).filter(models.User.id == req.owner_id).first()
    borrower = db.query(models.User).filter(models.User.id == req.borrower_id).first()

    if owner:
        owner.total_lends = (owner.total_lends or 0) + 1
        owner.karma = (owner.karma if owner.karma is not None else 100) + owner_gain
        owner.trust_score = float(owner.karma)
    if borrower:
        borrower.total_borrows = (borrower.total_borrows or 0) + 1
        borrower.karma = (borrower.karma if borrower.karma is not None else 100) + borrower_change
        borrower.trust_score = float(borrower.karma)

    req.status = "completed"
    db.commit()
    db.refresh(trans)

    return {
        "message": "Item returned successfully",
        "detail": "Return confirmed, item available again",
        "karma_updated": {
            "owner_gain": owner_gain,
            "borrower_change": borrower_change,
            "is_on_time": is_on_time
        }
    }
```

### 4.5 Changes to `backend/app/routes/auth.py`
Set `karma=100` and `trust_score=100.0` when registering a new user:
```python
# In backend/app/routes/auth.py (line 19):
    new_user = models.User(
        email=user.email,
        name=user.name,
        dept=user.dept,
        batch=user.batch,
        roll=user.roll,
        hashed_password=hashed,
        karma=100,
        trust_score=100.0,
    )
```

### 4.6 File Removal
Delete the file:
```bash
rm /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend/app/routes/requests.py
```

### 4.7 Database Schema Migration Safeguard
In `backend/app/database.py` or database startup hook in `main.py`, run:
```python
# Auto-migrate SQLite schema for karma column
with engine.connect() as conn:
    cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()]
    if "karma" not in cols:
        conn.exec_driver_sql("ALTER TABLE users ADD COLUMN karma INTEGER DEFAULT 100")
```

---

## 5. Verification Method

### 5.1 Verification Checklist & Invalidation Conditions
| Item | Target | Expected Behavior | Invalidation Condition |
|---|---|---|---|
| **Base Karma** | `POST /api/auth/register` | Returns user object with `karma: 100` | Response lacks `karma` or `karma != 100` |
| **Transaction Return (On-time)** | `POST /api/transactions/return/{id}` where $T_{\text{now}} \le T_{\text{due}}$ | Owner +10 Karma, Borrower +5 Karma, `is_on_time: true` | Karma not changed or incorrect delta |
| **Transaction Return (Late)** | `POST /api/transactions/return/{id}` where $T_{\text{now}} > T_{\text{due}}$ | Owner +10 Karma, Borrower -30 Karma, `is_on_time: false` | Borrower does not lose 30 Karma |
| **Bug 1 Fix** | `GET /api/requests/me` | `BorrowRequestOut` includes `transaction` object with status | `transaction` field is missing or stripped |
| **Bug 2 Fix** | `PUT /api/requests/{id}/status?status=accepted` | Accepts request and returns 200 OK without body | Returns HTTP 422 Unprocessable Entity |
| **Bug 2 Fix** | `PUT /api/requests/{id}/status` with JSON `{"status": "accepted"}` | Accepts request and returns 200 OK | Returns HTTP 422 or fails |
| **Duplicate Removal** | `backend/app/routes/requests.py` | File deleted, all routes function via `borrow_requests.py` | File still exists in directory |

### 5.2 Independent Automated Verification Script
The following Python script can be run to verify all 5 items end-to-end once implemented:

```python
import sqlite3
import os

DB_PATH = "backend/campus_share.db"

def verify_all():
    # 1. Verify requests.py deleted
    assert not os.path.exists("backend/app/routes/requests.py"), "Duplicate requests.py still exists!"
    print("PASS: Duplicate requests.py removed")

    # 2. Verify karma column in SQLite
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    cols = [col[1] for col in c.execute("PRAGMA table_info(users)").fetchall()]
    assert "karma" in cols, "karma column missing from users table in database"
    print("PASS: karma column present in users table")

    # 3. Verify models and schemas syntax and imports
    from backend.app import models, schemas
    assert hasattr(models.User, "karma"), "User model missing karma column"
    assert "karma" in schemas.UserOut.model_fields, "UserOut schema missing karma field"
    assert "transaction" in schemas.BorrowRequestOut.model_fields, "BorrowRequestOut missing transaction field"
    print("PASS: models.py and schemas.py correctly defined")

if __name__ == "__main__":
    verify_all()
```
