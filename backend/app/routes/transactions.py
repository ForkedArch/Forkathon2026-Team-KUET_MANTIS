from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models, auth, database
from ..utils.qr_code import generate_qr_base64
import random
import string
from datetime import datetime, timezone

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

@router.post("/start")
def start_transaction(
    data: schemas.TransactionStart,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
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
