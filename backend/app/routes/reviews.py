from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from .. import schemas, models, auth, database

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("", response_model=schemas.ReviewOut)
@router.post("/", response_model=schemas.ReviewOut)
def create_review(
    review_in: schemas.ReviewCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if review_in.reviewee_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot review yourself")

    reviewee = db.query(models.User).filter(models.User.id == review_in.reviewee_id).first()
    if not reviewee:
        raise HTTPException(status_code=404, detail="Student being reviewed not found")

    review = models.Review(
        transaction_id=review_in.transaction_id,
        reviewer_id=current_user.id,
        reviewee_id=review_in.reviewee_id,
        rating=review_in.rating,
        comment=review_in.comment,
    )
    db.add(review)

    # Send notification to reviewee
    notif = models.Notification(
        user_id=review_in.reviewee_id,
        title=f"New {review_in.rating}-star review from {current_user.name}",
        message=review_in.comment or f"Rated you {review_in.rating}/5 stars",
        link=f"/profile",
    )
    db.add(notif)

    db.commit()
    db.refresh(review)
    review.reviewer = current_user
    return review


@router.get("/user/{user_id}", response_model=List[schemas.ReviewOut])
def get_user_reviews(
    user_id: int,
    db: Session = Depends(database.get_db),
):
    return (
        db.query(models.Review)
        .options(joinedload(models.Review.reviewer))
        .filter(models.Review.reviewee_id == user_id)
        .order_by(models.Review.created_at.desc())
        .all()
    )
