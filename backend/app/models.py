from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON, UniqueConstraint
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
    roll = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=True)  # simplified
    karma = Column(Integer, default=100, nullable=False)
    trust_score = Column(Float, default=100.0)
    total_lends = Column(Integer, default=0)
    total_borrows = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        UniqueConstraint('batch', 'dept', 'roll', name='uq_user_batch_dept_roll'),
    )

    items = relationship("Item", back_populates="owner", cascade="all, delete-orphan")
    sent_requests = relationship("BorrowRequest", foreign_keys="BorrowRequest.borrower_id", back_populates="borrower")
    received_requests = relationship("BorrowRequest", foreign_keys="BorrowRequest.owner_id", back_populates="owner")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    type = Column(String, default="lend")  # "lend" or "borrow"
    description = Column(Text, nullable=True)
    specs = Column(Text, nullable=True)
    condition = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    zone = Column(String, nullable=True)
    zone_id = Column(String, nullable=True)
    tags = Column(JSON, default=list, nullable=True)
    status = Column(String, default="available")  # "available", "borrowed", "beacon"
    is_available = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=utcnow)

    @property
    def lat(self):
        return self.latitude

    @property
    def lng(self):
        return self.longitude

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
    request_id = Column(Integer, ForeignKey("borrow_requests.id"), nullable=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    request = relationship("BorrowRequest")
    sender = relationship("User", foreign_keys=[sender_id])
    recipient = relationship("User", foreign_keys=[recipient_id])
    item = relationship("Item", foreign_keys=[item_id])

class SavedItem(Base):
    __tablename__ = "saved_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'item_id', name='uq_user_saved_item'),
    )

    user = relationship("User")
    item = relationship("Item")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewee_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1 to 5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    reviewer = relationship("User", foreign_keys=[reviewer_id])
    reviewee = relationship("User", foreign_keys=[reviewee_id])

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=utcnow)

    reporter = relationship("User", foreign_keys=[reporter_id])
    item = relationship("Item", foreign_keys=[item_id])

