from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models import UserRole, ComplaintStatus, ComplaintPriority, HistoryEventType


# ---------- Auth ----------

class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    flat_number: Optional[str] = Field(default=None, max_length=30)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    role: UserRole
    flat_number: Optional[str] = None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Complaint history ----------

class ComplaintHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    event_type: HistoryEventType
    previous_status: Optional[ComplaintStatus] = None
    new_status: Optional[ComplaintStatus] = None
    previous_priority: Optional[ComplaintPriority] = None
    new_priority: Optional[ComplaintPriority] = None
    note: Optional[str] = None
    actor_name: str
    created_at: datetime


# ---------- Complaints ----------

class ComplaintCreate(BaseModel):
    category: str = Field(min_length=2, max_length=60)
    description: str = Field(min_length=10, max_length=4000)


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference_code: str
    category: str
    description: str
    photo_path: Optional[str] = None
    status: ComplaintStatus
    priority: ComplaintPriority
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    resident_id: int
    resident_name: Optional[str] = None
    is_overdue: bool = False
    days_open: int = 0
    sla_message: str = ""


class ComplaintDetailOut(ComplaintOut):
    history: List[ComplaintHistoryOut] = []


class StatusUpdate(BaseModel):
    status: ComplaintStatus
    note: Optional[str] = Field(default=None, max_length=1000)


class PriorityUpdate(BaseModel):
    priority: ComplaintPriority
    note: Optional[str] = Field(default=None, max_length=1000)


# ---------- Notices ----------

class NoticeCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=3, max_length=4000)
    is_important: bool = False


class NoticeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    content: str
    is_important: bool
    author_name: str
    created_at: datetime


# ---------- Dashboard ----------

class DashboardOut(BaseModel):
    total_complaints: int
    open_count: int
    in_progress_count: int
    resolved_count: int
    overdue_count: int
    overdue_high_priority_count: int
    by_category: dict
    by_priority: dict
    overdue_threshold_days: int


# ---------- Generic ----------

class ErrorResponse(BaseModel):
    detail: str
