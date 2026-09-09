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
    status: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    req = db.query(models.BorrowRequest).filter(models.BorrowRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can change status")
    if status not in ["accepted", "declined"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    req.status = status
    db.commit()
    # If accepted, mark item as unavailable
    if status == "accepted":
        item = db.query(models.Item).filter(models.Item.id == req.item_id).first()
        if item:
            item.is_available = False
            db.commit()
    return {"detail": f"Request {status}"}