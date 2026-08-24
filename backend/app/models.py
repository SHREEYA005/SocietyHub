"""
Database models.

Design notes:
- ComplaintHistory is an append-only audit trail: rows are never updated or
  deleted, only inserted. It captures status changes, priority changes and
  free-text notes so the full lifecycle of a complaint can be reconstructed.
- Overdue status is intentionally NOT stored as a column. It is a derived
  value (created_at + threshold vs. now, excluding RESOLVED complaints) so
  it can never drift out of sync with the configured threshold. See
  app/services/overdue.py.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
)
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, enum.Enum):
    RESIDENT = "resident"
    ADMIN = "admin"


class ComplaintStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


class ComplaintPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class HistoryEventType(str, enum.Enum):
    CREATED = "CREATED"
    STATUS_CHANGE = "STATUS_CHANGE"
    PRIORITY_CHANGE = "PRIORITY_CHANGE"
    NOTE = "NOTE"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.RESIDENT)
    flat_number = Column(String(30), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    complaints = relationship("Complaint", back_populates="resident", foreign_keys="Complaint.resident_id")


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    reference_code = Column(String(30), unique=True, nullable=False, index=True)

    resident_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    category = Column(String(60), nullable=False, index=True)
    description = Column(Text, nullable=False)
    photo_path = Column(String(500), nullable=True)

    status = Column(Enum(ComplaintStatus), nullable=False, default=ComplaintStatus.OPEN, index=True)
    priority = Column(Enum(ComplaintPriority), nullable=False, default=ComplaintPriority.MEDIUM, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    resident = relationship("User", back_populates="complaints", foreign_keys=[resident_id])
    history = relationship(
        "ComplaintHistory",
        back_populates="complaint",
        order_by="ComplaintHistory.created_at",
        cascade="all, delete-orphan",
    )

    @staticmethod
    def generate_reference_code() -> str:
        year = datetime.utcnow().year
        suffix = uuid.uuid4().hex[:6].upper()
        return f"SMT-{year}-{suffix}"


class ComplaintHistory(Base):
    """Append-only audit trail. No update/delete operations are exposed via the API."""
    __tablename__ = "complaint_history"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(Enum(HistoryEventType), nullable=False)
    previous_status = Column(Enum(ComplaintStatus), nullable=True)
    new_status = Column(Enum(ComplaintStatus), nullable=True)
    previous_priority = Column(Enum(ComplaintPriority), nullable=True)
    new_priority = Column(Enum(ComplaintPriority), nullable=True)

    note = Column(Text, nullable=True)

    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    actor_name = Column(String(120), nullable=False)  # denormalized snapshot at time of event

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    complaint = relationship("Complaint", back_populates="history")


class Notice(Base):
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    is_important = Column(Boolean, default=False, nullable=False, index=True)

    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    author_name = Column(String(120), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
