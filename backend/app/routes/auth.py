import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .. import schemas, models, auth, database

router = APIRouter(prefix="/api/auth", tags=["auth"])


def decode_kuet_email(email: str):
    email_clean = email.strip().lower()
    if not email_clean.endswith("@stud.kuet.ac.bd"):
        raise HTTPException(
            status_code=400,
            detail="Only @stud.kuet.ac.bd email addresses are allowed"
        )
    local_part = email_clean.split("@")[0]
    match = re.search(r'(\d{2})(\d{2})(\d{3})$', local_part, re.ASCII)
    if not match:
        raise HTTPException(
            status_code=400,
            detail="Invalid KUET student email: must end with 7-digit student ID: 2-digit batch, 2-digit dept, 3-digit roll (e.g. siddique2307010@stud.kuet.ac.bd)"
        )
    batch, dept, roll = match.groups()
    return batch, dept, roll


@router.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserRegister, db: Session = Depends(database.get_db)):
    email_clean = user.email.strip().lower()
    batch, dept, roll = decode_kuet_email(email_clean)

    # Check if email already registered
    db_user = db.query(models.User).filter(models.User.email == email_clean).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check composite uniqueness (batch, dept, roll)
    db_roll = db.query(models.User).filter(
        models.User.batch == batch,
        models.User.dept == dept,
        models.User.roll == roll
    ).first()
    if db_roll:
        raise HTTPException(status_code=400, detail="Roll number already registered for this batch and department")

    # Create new user with 100 Base Karma
    hashed = auth.get_password_hash(user.password)
    new_user = models.User(
        email=email_clean,
        name=user.name.strip(),
        dept=dept,
        batch=batch,
        roll=roll,
        hashed_password=hashed,
        karma=100,
        trust_score=100.0,
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email or roll number already registered for this batch and department"
        )
    return new_user


@router.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(database.get_db)):
    email_clean = user.email.strip().lower()
    db_user = db.query(models.User).filter(models.User.email == email_clean).first()
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": str(db_user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }


@router.get("/me", response_model=schemas.UserOut)
def get_current_user_info(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@router.get("/current", response_model=schemas.UserOut)
def get_current_user_alias(current_user: models.User = Depends(auth.get_current_user)):
    return current_user
