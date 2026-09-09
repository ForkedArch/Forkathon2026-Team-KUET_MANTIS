from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, models, auth, database

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.get("/{request_id}/messages", response_model=List[schemas.MessageOut])
def get_messages(
    request_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Check if user is part of this request
    req = db.query(models.BorrowRequest).filter(models.BorrowRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.borrower_id != current_user.id and req.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Only allow if request is accepted or completed (to simulate chat unlock)
    if req.status not in ["accepted", "completed"]:
        # You can optionally allow only after accepted
        raise HTTPException(status_code=403, detail="Chat not unlocked yet")
    messages = db.query(models.Message).filter(models.Message.request_id == request_id).order_by(models.Message.created_at).all()
    return messages

@router.post("/{request_id}/messages", response_model=schemas.MessageOut)
def send_message(
    request_id: int,
    msg: schemas.MessageCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    req = db.query(models.BorrowRequest).filter(models.BorrowRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.borrower_id != current_user.id and req.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if req.status not in ["accepted", "completed"]:
        raise HTTPException(status_code=403, detail="Chat not unlocked")
    new_msg = models.Message(
        request_id=request_id,
        sender_id=current_user.id,
        content=msg.content
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return new_msg
