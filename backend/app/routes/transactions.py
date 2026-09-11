from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models, auth, database
from ..utils.qr_code import generate_qr_base64
import random
import string
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

@router.post("/start")
def start_transaction(
    data: schemas.TransactionStart,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Initiates physical item handover for an accepted borrow request.
    Generates a secure 4-digit OTP and scannable QR code for in-person verification.
    Only the item owner can initiate handover.
    """
    req = db.query(models.BorrowRequest).filter(models.BorrowRequest.id == data.request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can start handover")
    if req.status != "accepted":
        raise HTTPException(status_code=400, detail="Request not accepted")
    # Generate OTP (4 digits)
    otp = ''.join(random.choices(string.digits, k=4))
    # Generate QR code (data includes request_id and otp)
    qr_data = f"{data.request_id}:{otp}"
    qr_base64 = generate_qr_base64(qr_data)
    # Create or update transaction
    trans = db.query(models.Transaction).filter(models.Transaction.request_id == data.request_id).first()
    if trans and trans.status in ["borrowed", "returned"]:
        raise HTTPException(status_code=400, detail="Transaction is already in progress or completed")
    if not trans:
        trans = models.Transaction(request_id=data.request_id)
        db.add(trans)
    trans.otp = otp
    trans.qr_code = qr_base64
    trans.status = "pending"
    db.commit()
    db.refresh(trans)
    return {"otp": otp, "qr_code": qr_base64, "transaction_id": trans.id}

@router.post("/verify")
def verify_handover(
    data: schemas.TransactionVerify,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Verifies physical item handover using the borrower-submitted 4-digit OTP.
    Transitions transaction status to 'borrowed' and clears one-time OTP.
    Only the designated borrower can verify handover.
    """
    req = db.query(models.BorrowRequest).filter(models.BorrowRequest.id == data.request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.borrower_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only borrower can verify")
    trans = db.query(models.Transaction).filter(models.Transaction.request_id == data.request_id).first()
    if not trans:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if trans.status != "pending":
        raise HTTPException(status_code=400, detail="Transaction is not pending verification")
    if not trans.otp or trans.otp != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    trans.status = "borrowed"
    trans.borrowed_at = datetime.now(timezone.utc)
    trans.otp = None
    trans.qr_code = None
    # Update item status (already unavailable from accept)
    db.commit()
    return {"detail": "Handover verified, item borrowed"}

@router.post("/return/{request_id}")
def request_return(
    request_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Completes return of a borrowed item and executes KUET Karma Protocol awards:
    - Item availability is restored to the campus inventory.
    - Owner is awarded +10 KUET Karma for successful lending.
    - Borrower is awarded +5 Karma if returned on-time, or penalized -30 Karma if overdue.
    - Request lifecycle transitions to 'completed'.
    """
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
        item.status = "available"

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

