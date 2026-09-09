from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str
    dept: str
    batch: str
    roll: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trust_score: float
    total_lends: int
    total_borrows: int
    created_at: datetime

# Token
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# Item schemas
class ItemBase(BaseModel):
    title: str
    category: str
    description: Optional[str] = None
    condition: Optional[str] = None
    zone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_available: bool = True

class ItemCreate(ItemBase):
    pass

class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: Optional[str] = None
    owner_id: int
    created_at: datetime
    owner: UserOut

# Request schemas
class BorrowRequestCreate(BaseModel):
    item_id: int
    duration_hours: int
    purpose: Optional[str] = None
    pickup_zone: Optional[str] = None
    message: Optional[str] = None

class BorrowRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    borrower_id: int
    owner_id: int
    duration_hours: int
    purpose: Optional[str]
    pickup_zone: Optional[str]
    message: Optional[str]
    status: str
    created_at: datetime
    item: ItemOut
    borrower: UserOut
    owner: UserOut

# Explicit JSON body for status updates, instead of a raw query-string
# "status" parameter, so this endpoint matches the JSON-body convention
# used by the rest of the API and validates the allowed values up front.
class BorrowRequestStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"accepted", "declined"}
        if v not in allowed:
            raise ValueError(f"status must be one of {sorted(allowed)}")
        return v

# Transaction schemas
class TransactionStart(BaseModel):
    request_id: int

class TransactionVerify(BaseModel):
    request_id: int
    otp: str

# Message schemas
class MessageCreate(BaseModel):
    content: str

class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    sender_id: int
    content: str
    created_at: datetime
    sender: UserOut
