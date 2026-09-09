from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    dept = Column(String, nullable=False)
    batch = Column(String, nullable=False)
    roll = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=True)  # simplified
    trust_score = Column(Float, default=4.5)
    total_lends = Column(Integer, default=0)
    total_borrows = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    items = relationship("Item", back_populates="owner", cascade="all, delete-orphan")
    sent_requests = relationship("BorrowRequest", foreign_keys="BorrowRequest.borrower_id", back_populates="borrower")
    received_requests = relationship("BorrowRequest", foreign_keys="BorrowRequest.owner_id", back_populates="owner")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    condition = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    zone = Column(String, nullable=True)
    is_available = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=utcnow)

    owner = relationship("User", back_populates="items")
    requests = relationship("BorrowRequest", back_populates="item", cascade="all, delete-orphan")

class BorrowRequest(Base):
    __tablename__ = "borrow_requests"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    borrower_id = Column(Integer, ForeignKey("users.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    duration_hours = Column(Integer, nullable=False)
    purpose = Column(String, nullable=True)
    pickup_zone = Column(String, nullable=True)
    message = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, accepted, declined, completed
    created_at = Column(DateTime, default=utcnow)

    item = relationship("Item", back_populates="requests")
    borrower = relationship("User", foreign_keys=[borrower_id], back_populates="sent_requests")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="received_requests")
    transaction = relationship("Transaction", back_populates="request", uselist=False)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("borrow_requests.id"))
    otp = Column(String, nullable=True)
    qr_code = Column(Text, nullable=True)  # base64 or URL
    borrowed_at = Column(DateTime, nullable=True)
    returned_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  # pending, borrowed, returned

    request = relationship("BorrowRequest", back_populates="transaction")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("borrow_requests.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    request = relationship("BorrowRequest")
    sender = relationship("User")
