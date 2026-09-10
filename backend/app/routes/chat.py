from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from .. import schemas, models, auth, database

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _get_request_or_404(db: Session, request_id: int) -> models.BorrowRequest:
    req = db.query(models.BorrowRequest).filter(models.BorrowRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req


def _assert_participant(req: models.BorrowRequest, current_user: models.User):
    if req.borrower_id != current_user.id and req.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")


def _assert_chat_unlocked(req: models.BorrowRequest):
    if req.status not in ["accepted", "completed"]:
        raise HTTPException(status_code=403, detail="Chat not unlocked yet")


@router.get("/{request_id}/messages", response_model=List[schemas.MessageOut])
def get_messages(
    request_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    req = _get_request_or_404(db, request_id)
    _assert_participant(req, current_user)
    _assert_chat_unlocked(req)

    messages = (
        db.query(models.Message)
        .options(joinedload(models.Message.sender))
        .filter(models.Message.request_id == request_id)
        .order_by(models.Message.created_at)
        .all()
    )
    return messages


@router.post("/{request_id}/messages", response_model=schemas.MessageOut)
def send_message(
    request_id: int,
    msg: schemas.MessageCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    req = _get_request_or_404(db, request_id)
    _assert_participant(req, current_user)
    _assert_chat_unlocked(req)

    content = (msg.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    new_msg = models.Message(
        request_id=request_id,
        sender_id=current_user.id,
        content=content,
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    new_msg.sender = current_user
    return new_msg
