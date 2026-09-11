from pydantic import BaseModel, EmailStr, ConfigDict, field_validator, model_validator, Field
from datetime import datetime
from typing import Optional, List, Any

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str
    dept: Optional[str] = None
    batch: Optional[str] = None
    roll: Optional[str] = None

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=4)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name cannot be empty or whitespace only")
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()

UserCreate = UserRegister  # Alias for backward compatibility

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    karma: int = 100
    trust_score: Optional[float] = 100.0
    total_lends: int = 0
    total_borrows: int = 0
    created_at: datetime

    @field_validator("dept", mode="before")
    @classmethod
    def normalize_dept(cls, v):
        if not v:
            return v
        cleaned = str(v).strip()
        if cleaned.isdigit():
            from .routes.auth import decode_dept_code
            return decode_dept_code(cleaned)
        return cleaned

# Token
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# Landmarks schemas
class CampusMetadata(BaseModel):
    name: str
    center: List[float]
    boundary_radius_meters: int = 700
    zoom_default: float = 16.5
    description: Optional[str] = None

class CampusZone(BaseModel):
    id: str
    name: str
    category: str
    coords: List[float]
    floors: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    popular_items: Optional[List[str]] = None

class LandmarksResponse(BaseModel):
    success: bool = True
    campus: CampusMetadata
    zones: List[CampusZone]

# Item schemas
class ItemBase(BaseModel):
    title: str
    category: str
    type: str = "lend"  # "lend" or "borrow"
    description: Optional[str] = None
    specs: Optional[str] = None
    condition: Optional[str] = None
    zone: Optional[str] = None
    zone_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    tags: Optional[List[str]] = []
    status: Optional[str] = "available"
    is_available: bool = True

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Title is required and cannot be empty")
        return v.strip()

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("lend", "borrow"):
            raise ValueError("Item type must be 'lend' or 'borrow'")
        return v

class ItemCreate(ItemBase):
    pass

class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: Optional[str] = None
    image: Optional[str] = None
    owner_id: int
    created_at: datetime
    owner: Optional[UserOut] = None
    lender_name: Optional[str] = None
    karma: Optional[int] = None
    trust_rating: Optional[float] = None
    dept: Optional[str] = None
    roll: Optional[str] = None
    batch: Optional[str] = None
    coords: Optional[List[float]] = None

    @model_validator(mode='after')
    def normalize_fields(self) -> 'ItemOut':
        # Coordinate normalization
        if self.lat is None and self.latitude is not None:
            self.lat = self.latitude
        if self.lng is None and self.longitude is not None:
            self.lng = self.longitude
        if self.latitude is None and self.lat is not None:
            self.latitude = self.lat
        if self.longitude is None and self.lng is not None:
            self.longitude = self.lng
        if self.coords is None and self.lng is not None and self.lat is not None:
            self.coords = [self.lng, self.lat]

        # Field aliases
        if self.image is None and self.image_url is not None:
            self.image = self.image_url
        if self.zone_id is None and self.zone is not None:
            self.zone_id = self.zone
        if self.zone is None and self.zone_id is not None:
            self.zone = self.zone_id

        # Populate owner fields
        if self.owner:
            self.lender_name = self.owner.name
            self.dept = self.owner.dept
            self.roll = self.owner.roll
            self.batch = self.owner.batch
            self.karma = getattr(self.owner, 'karma', 100)
            self.trust_rating = getattr(self.owner, 'trust_score', 100.0)

        if self.dept and str(self.dept).strip().isdigit():
            from .routes.auth import decode_dept_code
            self.dept = decode_dept_code(self.dept)

        return self

# Transaction schemas
class TransactionStart(BaseModel):
    request_id: int

class TransactionVerify(BaseModel):
    request_id: int
    otp: str

class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    otp: Optional[str] = None
    qr_code: Optional[str] = None
    borrowed_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    status: str

# Request schemas
class BorrowRequestCreate(BaseModel):
    item_id: int
    duration_hours: int = Field(..., gt=0, description="Duration in hours must be greater than 0")
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
    purpose: Optional[str] = None
    pickup_zone: Optional[str] = None
    message: Optional[str] = None
    status: str
    created_at: datetime
    item: ItemOut
    borrower: UserOut
    owner: UserOut
    transaction: Optional[TransactionOut] = None

class BorrowRequestStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"accepted", "declined"}
        if v not in allowed:
            raise ValueError(f"status must be one of {sorted(allowed)}")
        return v

# Message schemas
class MessageCreate(BaseModel):
    content: str
    recipient_id: Optional[int] = None
    item_id: Optional[int] = None

class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: Optional[int] = None
    sender_id: int
    recipient_id: Optional[int] = None
    item_id: Optional[int] = None
    content: str
    is_read: bool = False
    created_at: datetime
    sender: UserOut
    recipient: Optional[UserOut] = None

class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contact: UserOut
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    request_id: Optional[int] = None
    item_id: Optional[int] = None


# Wishlist / Saved Items schemas
class SavedItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    item_id: int
    created_at: datetime
    item: ItemOut

# Notification schemas
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    title: str
    message: str
    link: Optional[str] = None
    is_read: bool = False
    created_at: datetime

# Review schemas
class ReviewCreate(BaseModel):
    reviewee_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    transaction_id: Optional[int] = None

class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reviewer_id: int
    reviewee_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    reviewer: UserOut

# Report schemas
class ReportCreate(BaseModel):
    reason: str
    details: Optional[str] = None

class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    item_id: int
    reporter_id: int
    reason: str
    details: Optional[str] = None
    status: str
    created_at: datetime

# Item Update schema
class ItemUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    specs: Optional[str] = None
    condition: Optional[str] = None
    zone: Optional[str] = None
    is_available: Optional[bool] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None

