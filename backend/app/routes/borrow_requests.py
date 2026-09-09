from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, models, auth, database

router = APIRouter(prefix="/api/requests", tags=["requests"])

@router.post("/", response_model=schemas.BorrowRequestOut)
def create_request(
    req: schemas.BorrowRequestCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Check if item exists and is available
    item = db.query(models.Item).filter(models.Item.id == req.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not item.is_available:
        raise HTTPException(status_code=400, detail="Item not available")
    if item.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot request your own item")
    # Prevent the same borrower from spamming multiple pending requests for
    # the same item.
    existing = db.query(models.BorrowRequest).filter(
        models.BorrowRequest.item_id == req.item_id,
        models.BorrowRequest.borrower_id == current_user.id,
        models.BorrowRequest.status == "pending",
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already have a pending request for this item")
    # Create request
    new_request = models.BorrowRequest(
        item_id=req.item_id,
        borrower_id=current_user.id,
        owner_id=item.owner_id,
        duration_hours=req.duration_hours,
        purpose=req.purpose,
        pickup_zone=req.pickup_zone,
        message=req.message,
        status="pending"
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request

@router.get("/me", response_model=List[schemas.BorrowRequestOut])
def get_my_requests(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Get requests where user is borrower OR owner
    requests = db.query(models.BorrowRequest).filter(
        (models.BorrowRequest.borrower_id == current_user.id) |
        (models.BorrowRequest.owner_id == current_user.id)
    ).order_by(models.BorrowRequest.created_at.desc()).all()
    return requests

@router.put("/{request_id}/status")
def update_request_status(
    request_id: int,
    body: schemas.BorrowRequestStatusUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    status = body.status  # already validated to be "accepted" or "declined"

    req = db.query(models.BorrowRequest).filter(models.BorrowRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can change status")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="This request has already been resolved")

    if status == "accepted":
        # Re-check availability right before accepting: without this, two
        # pending requests for the same item could both be accepted by the
        # owner (e.g. from two open browser tabs), leaving the item "lent"
        # to two different borrowers at once.
        item = db.query(models.Item).filter(models.Item.id == req.item_id).first()
        if not item or not item.is_available:
            raise HTTPException(status_code=400, detail="Item is no longer available")

        req.status = "accepted"
        item.is_available = False

        # Auto-decline any other still-pending requests for this item so
        # they don't linger as if they were still actionable.
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

    return {"detail": f"Request {status}"}
