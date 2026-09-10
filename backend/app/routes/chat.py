from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc
from typing import List, Optional
from datetime import datetime, timezone
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


@router.get("/conversations", response_model=List[schemas.ConversationOut])
def get_conversations(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """List all active conversations for the current user (direct & request-based)."""
    # Fetch all messages where current_user is sender, recipient, or participant in request
    messages = (
        db.query(models.Message)
        .options(
            joinedload(models.Message.sender),
            joinedload(models.Message.recipient),
            joinedload(models.Message.request).joinedload(models.BorrowRequest.borrower),
            joinedload(models.Message.request).joinedload(models.BorrowRequest.owner),
        )
        .filter(
            or_(
                models.Message.sender_id == current_user.id,
                models.Message.recipient_id == current_user.id,
                models.Message.request.has(
                    or_(
                        models.BorrowRequest.borrower_id == current_user.id,
                        models.BorrowRequest.owner_id == current_user.id,
                    )
                ),
            )
        )
        .order_by(desc(models.Message.created_at))
        .all()
    )

    conversations = {}
    for m in messages:
        # Determine peer
        peer = None
        req_id = m.request_id
        item_id = m.item_id

        if m.recipient_id:
            peer = m.recipient if m.sender_id == current_user.id else m.sender
        elif m.request:
            peer = m.request.owner if m.request.borrower_id == current_user.id else m.request.borrower
            if not item_id and m.request.item_id:
                item_id = m.request.item_id

        if not peer or peer.id == current_user.id:
            continue

        if peer.id not in conversations:
            unread = 0
            conversations[peer.id] = {
                "contact": peer,
                "last_message": m.content,
                "last_message_at": m.created_at,
                "unread_count": 1 if (m.recipient_id == current_user.id and not m.is_read) else 0,
                "request_id": req_id,
                "item_id": item_id,
            }
        else:
            if m.recipient_id == current_user.id and not m.is_read:
                conversations[peer.id]["unread_count"] += 1

    def _conv_time(c):
        t = c.get("last_message_at")
        if not t:
            return datetime.min
        return t.replace(tzinfo=None) if hasattr(t, "tzinfo") and t.tzinfo else t

    return sorted(conversations.values(), key=_conv_time, reverse=True)


@router.get("/direct/{other_user_id}", response_model=List[schemas.MessageOut])
def get_direct_messages(
    other_user_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Get 1:1 message history with another student."""
    other_user = db.query(models.User).filter(models.User.id == other_user_id).first()
    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch direct messages between the two users
    messages = (
        db.query(models.Message)
        .options(
            joinedload(models.Message.sender),
            joinedload(models.Message.recipient),
        )
        .filter(
            or_(
                and_(models.Message.sender_id == current_user.id, models.Message.recipient_id == other_user_id),
                and_(models.Message.sender_id == other_user_id, models.Message.recipient_id == current_user.id),
                # Also include messages from shared borrow requests between these two users
                and_(
                    models.Message.request.has(
                        or_(
                            and_(models.BorrowRequest.borrower_id == current_user.id, models.BorrowRequest.owner_id == other_user_id),
                            and_(models.BorrowRequest.borrower_id == other_user_id, models.BorrowRequest.owner_id == current_user.id),
                        )
                    )
                ),
            )
        )
        .order_by(models.Message.created_at)
        .all()
    )

    # Mark incoming unread messages as read
    for m in messages:
        if m.recipient_id == current_user.id and not m.is_read:
            m.is_read = True
    db.commit()

    return messages


@router.post("/direct/{other_user_id}", response_model=schemas.MessageOut)
def send_direct_message(
    other_user_id: int,
    msg: schemas.MessageCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Send a direct 1:1 message to another student."""
    if other_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot chat with yourself")

    other_user = db.query(models.User).filter(models.User.id == other_user_id).first()
    if not other_user:
        raise HTTPException(status_code=404, detail="Recipient student not found")

    content = (msg.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    new_msg = models.Message(
        sender_id=current_user.id,
        recipient_id=other_user_id,
        item_id=msg.item_id,
        content=content,
    )
    db.add(new_msg)

    # Trigger notification for recipient
    notif = models.Notification(
        user_id=other_user_id,
        title=f"New message from {current_user.name}",
        message=content[:100],
        link=f"/chat?user={current_user.id}",
    )
    db.add(notif)

    db.commit()
    db.refresh(new_msg)
    new_msg.sender = current_user
    new_msg.recipient = other_user
    return new_msg


# Legacy / Request-Specific Endpoints
@router.get("/{request_id}/messages", response_model=List[schemas.MessageOut])
def get_messages(
    request_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    req = _get_request_or_404(db, request_id)
    _assert_participant(req, current_user)

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

    content = (msg.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    recipient_id = req.owner_id if current_user.id == req.borrower_id else req.borrower_id
    new_msg = models.Message(
        request_id=request_id,
        sender_id=current_user.id,
        recipient_id=recipient_id,
        item_id=req.item_id,
        content=content,
    )
    db.add(new_msg)

    notif = models.Notification(
        user_id=recipient_id,
        title=f"Message regarding request #{req.id}",
        message=content[:100],
        link=f"/chat/{req.id}",
    )
    db.add(notif)

    db.commit()
    db.refresh(new_msg)
    new_msg.sender = current_user
    return new_msg

