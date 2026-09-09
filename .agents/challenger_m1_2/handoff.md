# Adversarial Challenge Report: KUET Karma Protocol & Transaction States

**Agent**: `challenger_m1_2`  
**Role**: Empirical Challenger / Critic / Specialist  
**Working Directory**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/challenger_m1_2`  
**Target Handoff File**: `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/challenger_m1_2/handoff.md`  
**Date**: 2026-09-10  
**Explicit Verdict**: **REQUEST_CHANGES**

---

## Executive Summary & Verdict

- **Verdict**: **REQUEST_CHANGES**
- **Overall Risk Assessment**: **CRITICAL**
- **Summary**:
  While the basic arithmetic (+10 owner, +5 on-time borrower, -30 late borrower), exact boundary timing comparison (`now <= due_time`), negative score serialization, and direct double-return prevention are implemented, **adversarial stress testing revealed two critical/high security flaws in the transaction state machine**:
  1. **[CRITICAL] Infinite Karma Mining Loop via Handover Re-verification Replay**: Calling `POST /api/transactions/verify` after an item has already been returned succeeds because `trans.status == "pending"` is not enforced and OTP is never invalidated. This resets `trans.status` back to `"borrowed"`, enabling the borrower to repeatedly call `POST /api/transactions/return/{request_id}` and arbitrarily mine infinite karma (+10 to owner, +5 to borrower per loop).
  2. **[HIGH] Late Penalty Evasion via Mid-Borrow Re-verification**: Overdue borrowers can call `POST /api/transactions/verify` with the existing OTP to reset `trans.borrowed_at = datetime.now(timezone.utc)` mid-borrow, turning a late return (-30 penalty) into an on-time return (+5 reward).
  3. **[HIGH] Owner Mid-Borrow Transaction Reset & Return Lockout**: Owners can call `POST /api/transactions/start` during an active borrow, resetting `trans.status = "pending"`, locking the borrower out of returning the item and trapping them into late penalties.
  4. **[MEDIUM] Unvalidated Negative Duration in Borrow Requests**: `duration_hours` accepts negative values (e.g. -5), causing instant -30 penalties upon return.

All 4 vulnerabilities were empirically reproduced and verified via automated test harness `backend/test_adversarial_karma.py`.

---

## 1. Observation

Direct observations from code inspection and empirical execution of `backend/test_adversarial_karma.py`:

### Observation 1: Replay Vulnerability in `backend/app/routes/transactions.py`
Lines 41-59 of `backend/app/routes/transactions.py`:
```python
@router.post("/verify")
def verify_handover(
    data: schemas.TransactionVerify,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    req = db.query(models.BorrowRequest).filter(models.BorrowRequest.id == data.request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.borrower_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only borrower can verify")
    trans = db.query(models.Transaction).filter(models.Transaction.request_id == data.request_id).first()
    if not trans or trans.otp != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    trans.status = "borrowed"
    trans.borrowed_at = datetime.now(timezone.utc)
    # Update item status (already unavailable from accept)
    db.commit()
    return {"detail": "Handover verified, item borrowed"}
```
- **Observed Behavior**:
  1. `verify_handover` never checks `trans.status == "pending"` or `req.status == "accepted"`.
  2. `return/{request_id}` (lines 76-79) sets `trans.status = "returned"` and `req.status = "completed"`, but leaves `trans.otp` untouched.
  3. A borrower sending `POST /api/transactions/verify` with the old OTP receives HTTP 200 `{"detail": "Handover verified, item borrowed"}` and `trans.status` changes back from `"returned"` to `"borrowed"`.
  4. Calling `POST /api/transactions/return/{request_id}` immediately after succeeds with HTTP 200, incrementing owner karma by +10 and borrower karma by +5 again.
  - Verbatim execution output from test probe:
    ```
    Probe: Re-verify after return accepted? -> Status: 200 (VULNERABLE=True)
    Probe: Second return after re-verify accepted? -> Status: 200 (EXPLOIT CONFIRMED=True)
    ```

### Observation 2: Late Penalty Evasion Clock Reset
- In `verify_handover` line 56:
  `trans.borrowed_at = datetime.now(timezone.utc)`
- When an active borrow is 24 hours overdue, calling `POST /api/transactions/verify` with the initial OTP updates `trans.borrowed_at` to the current instant.
- Subsequent return checks `is_on_time = (now <= due_time)`, which evaluates to `True`.
- Verbatim execution output:
  ```
  Probe: Late penalty evaded via re-verify? -> (VULNERABLE=True)
  Return outcome: {'owner_gain': 10, 'borrower_change': 5, 'is_on_time': True}
  ```

### Observation 3: Owner Mid-Borrow Transaction Reset Lockout
- In `start_transaction` lines 20-23:
  ```python
  if req.owner_id != current_user.id:
      raise HTTPException(status_code=403, detail="Only owner can start handover")
  if req.status != "accepted":
      raise HTTPException(status_code=400, detail="Request not accepted")
  ```
- When an item is actively borrowed (`trans.status == "borrowed"`), `req.status` remains `"accepted"`.
- If the owner calls `POST /api/transactions/start`, lines 34-37 generate a new OTP and set `trans.status = "pending"`.
- The borrower immediately loses the ability to return: `POST /api/transactions/return/{request_id}` returns HTTP 400 `{"detail": "Item not currently borrowed"}`.
- Verbatim execution output:
  ```
  Owner calling start while item is borrowed: status = 200
  Transaction status in DB after owner restarted: pending
  Borrower trying to return after owner restart: 400 {"detail":"Item not currently borrowed"}
  ```

### Observation 4: Boundary Timing Empirical Behavior
- Inspected lines 87-94 of `transactions.py`:
  ```python
  borrowed_at = trans.borrowed_at or now
  if borrowed_at.tzinfo is None:
      borrowed_at = borrowed_at.replace(tzinfo=timezone.utc)
  duration = req.duration_hours or 0
  due_time = borrowed_at + timedelta(hours=duration)
  is_on_time = (now <= due_time)
  ```
- **At exact due time (`now == due_time`)**: `now <= due_time` is `True` -> Borrower receives +5, Owner receives +10. (PASS)
- **1 second before due time (`now = due_time - 1s`)**: `now <= due_time` is `True` -> Borrower receives +5, Owner receives +10. (PASS)
- **1 second after due time (`now = due_time + 1s`)**: `now <= due_time` is `False` -> Borrower receives -30, Owner receives +10. (PASS)
- **7 days after due time (`now = due_time + 7d`)**: `now <= due_time` is `False` -> Borrower receives -30, Owner receives +10. (PASS)
- **Storage precision**: SQLite stores `DateTime` as a string without timezone (`2026-09-09 22:06:34.472462`), which SQLAlchemy parses as a naive datetime. The code safely replaces `tzinfo` with `timezone.utc`. There is zero grace period; any timestamp strictly greater than `due_time` (even by microseconds) is deemed late.

### Observation 5: Successive Transactions & Negative Karma Scoring
- Starting baseline: Owner = 100, Borrower = 100.
- 3 successive on-time returns:
  - Owner: 100 -> 110 -> 120 -> 130 (+10 each)
  - Borrower: 100 -> 105 -> 110 -> 115 (+5 each)
  - `trust_score` strictly tracks `float(karma)`.
- 5 successive late returns starting from 115:
  - Return 1: 115 - 30 = 85
  - Return 2: 85 - 30 = 55
  - Return 3: 55 - 30 = 25
  - Return 4: 25 - 30 = -5 (enters negative score)
  - Return 5: -5 - 30 = -35 (deep negative score)
- Serialization test:
  - `GET /api/auth/current` returns `user.karma = -35`, `user.trust_score = -35.0` without schema validation error.
  - `POST /api/items/` by a negative-karma user correctly outputs `karma = -35`, `trust_rating = -35.0` in `ItemOut`.
- Recovery test:
  - Returning on-time while at -35 karma increments score by +5 to -30.

### Observation 6: Double-Returns & Unauthorized Returns
- **Immediate double return**: Calling `POST /api/transactions/return/{request_id}` twice in succession fails with HTTP 400 `{"detail": "Item not currently borrowed"}` on the second attempt. Karma is not awarded twice.
- **Unauthenticated return**: Returns HTTP 403 `{"detail": "Not authenticated"}` (via FastAPI `HTTPBearer`).
- **Owner returning own item**: Returns HTTP 403 `{"detail": "Only borrower can request return"}`.
- **Unrelated third-party student**: Returns HTTP 403 `{"detail": "Only borrower can request return"}`.
- **Non-existent request ID**: Returns HTTP 404 `{"detail": "Request not found"}`.
- **Return before handover verification**: Returns HTTP 400 `{"detail": "Item not currently borrowed"}`.

---

## 2. Logic Chain

1. **State Machine Invariants**:
   A secure lending transaction lifecycle must be a strictly forward-progressing directed acyclic graph:
   `pending -> accepted -> borrowed -> returned/completed`.
2. **Replay Vulnerability Cause**:
   In `transactions.py:41-59`, `verify_handover` assumes it will only be called once when `status == "pending"`. Because it lacks `if trans.status != "pending": raise HTTPException(400)`, any caller with the original OTP can re-trigger this transition at any time.
3. **Exploit Consequence**:
   Because `return/{request_id}` does not invalidate the OTP (e.g. setting `trans.otp = None`), an attacker can toggle between `verify` and `return`. Since each return grants +10 and +5 karma, a student can script 1,000 cycles in seconds and elevate their karma to 10,000+.
4. **Late Evasion Cause**:
   Updating `trans.borrowed_at = datetime.now(timezone.utc)` unconditionally on every call to `/verify` allows a borrower who is days late to refresh their borrowing start timestamp right before returning, completely evading the -30 penalty mandated by Requirement R4.
5. **Lockout Cause**:
   In `start_transaction`, checking only `req.status == "accepted"` is insufficient because `req.status` is never updated to `"borrowed"` when handover is verified. Therefore, `start_transaction` can be invoked even while `trans.status == "borrowed"`, allowing the owner to overwrite OTP and force the borrower into a locked, non-returnable state.
6. **Verdict Deduction**:
   Because the KUET Karma Protocol's integrity is easily subverted by these state machine bypasses, Milestone 1 cannot be approved in its current state. Changes must be requested and verified.

---

## 3. Caveats

- **Load / Concurrency**: Tests were executed using an asynchronous in-process ASGI client. High-volume concurrent requests hitting SQLite might experience brief table-level lock waits, but the state machine logic errors exist independently of concurrency.
- **Frontend Impact**: The vulnerabilities are backend API-level exploits; the React frontend does not expose a "re-verify" button in its intended UI flow, but any client or browser script can directly post to `/api/transactions/verify`.

---

## 4. Conclusion

**Verdict: REQUEST_CHANGES**

The implementation correctly fulfills the arithmetic rules of the KUET Karma Protocol (+10, +5, -30), handles boundary timings accurately, supports negative karma, and prevents naive direct double-returns. However, the transaction state machine contains critical flaws that allow OTP replay, infinite karma generation, late penalty evasion, and mid-borrow lockout.

### Required Changes for `worker_m1`:

1. **Fix `verify_handover` in `backend/app/routes/transactions.py`**:
   - Enforce that the transaction is in `"pending"` status before verification:
     ```python
     if trans.status != "pending":
         raise HTTPException(status_code=400, detail="Transaction is not pending verification")
     ```
   - Invalidate or clear the OTP after successful verification:
     ```python
     trans.otp = None
     trans.qr_code = None
     ```
2. **Fix `start_transaction` in `backend/app/routes/transactions.py`**:
   - Guard against restarting active or completed transactions:
     ```python
     if trans and trans.status in ["borrowed", "returned"]:
         raise HTTPException(status_code=400, detail="Transaction is already in progress or completed")
     ```
3. **Fix `BorrowRequestCreate` schema in `backend/app/schemas.py`**:
   - Validate that `duration_hours` is strictly positive:
     ```python
     from pydantic import Field
     ...
     duration_hours: int = Field(..., gt=0, description="Duration in hours must be greater than 0")
     ```

---

## 5. Verification Method

To independently reproduce the empirical findings and verify the fixes:

1. **Run the Adversarial Stress Test Suite**:
   ```bash
   python3 backend/test_adversarial_karma.py
   ```
   - **Current Output**: Reports `VULNERABLE=True` and `EXPLOIT CONFIRMED=True` for Suite 4 probes (4.1, 4.2, 4.3, 4.4).
   - **Expected Output after Fix**: Probes 4.1, 4.2, 4.3, and 4.4 should return HTTP 400/422 and report `VULNERABLE=False`.

2. **Run the Milestone 1 Regression Suite**:
   ```bash
   python3 backend/test_m1.py
   ```

3. **Run the Tanvir Campus Verification Suite**:
   ```bash
   python3 Tanvir/verify_campus_map.py
   ```

### Invalidation Conditions
- Calling `POST /api/transactions/verify` when `trans.status == "returned"` returns HTTP 200 instead of HTTP 400.
- Calling `POST /api/transactions/verify` when `trans.status == "borrowed"` returns HTTP 200 and updates `trans.borrowed_at`.
- Calling `POST /api/transactions/start` when `trans.status == "borrowed"` returns HTTP 200 and sets `trans.status = "pending"`.
- Submitting `POST /api/requests/` with `duration_hours: -5` returns HTTP 200 instead of HTTP 422.
