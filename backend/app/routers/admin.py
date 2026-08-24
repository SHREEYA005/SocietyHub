from datetime import datetime, date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.deps import require_admin
from app.models import Complaint, ComplaintStatus, ComplaintPriority, User
from app.schemas import ComplaintOut, DashboardOut
from app.services.overdue import is_overdue, days_open, sla_message
from app.config import get_settings
from app.routers.complaints import _to_out

router = APIRouter(prefix="/admin", tags=["Admin"])
settings = get_settings()


@router.get("/complaints", response_model=List[ComplaintOut])
def list_all_complaints(
    category: Optional[str] = None,
    status_filter: Optional[ComplaintStatus] = Query(default=None, alias="status"),
    priority: Optional[ComplaintPriority] = None,
    overdue_only: bool = False,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = db.query(Complaint)
    if category:
        query = query.filter(Complaint.category == category)
    if status_filter:
        query = query.filter(Complaint.status == status_filter)
    if priority:
        query = query.filter(Complaint.priority == priority)
    if date_from:
        query = query.filter(Complaint.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Complaint.created_at <= datetime.combine(date_to, datetime.max.time()))
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(
            (Complaint.reference_code.ilike(like)) | (Complaint.description.ilike(like))
        )

    complaints = query.order_by(Complaint.created_at.desc()).all()
    results = [_to_out(c) for c in complaints]
    if overdue_only:
        results = [r for r in results if r.is_overdue]

    # Priority-aware ordering: overdue + high priority rise to the top.
    priority_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    results.sort(key=lambda r: (not r.is_overdue, priority_rank.get(r.priority.value, 3), -r.created_at.timestamp()))
    return results


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    complaints = db.query(Complaint).all()

    total = len(complaints)
    open_count = sum(1 for c in complaints if c.status == ComplaintStatus.OPEN)
    in_progress_count = sum(1 for c in complaints if c.status == ComplaintStatus.IN_PROGRESS)
    resolved_count = sum(1 for c in complaints if c.status == ComplaintStatus.RESOLVED)

    overdue = [c for c in complaints if is_overdue(c)]
    overdue_high = [c for c in overdue if c.priority == ComplaintPriority.HIGH]

    by_category: dict = {}
    for c in complaints:
        by_category[c.category] = by_category.get(c.category, 0) + 1

    by_priority: dict = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    for c in complaints:
        by_priority[c.priority.value] = by_priority.get(c.priority.value, 0) + 1

    return DashboardOut(
        total_complaints=total,
        open_count=open_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        overdue_count=len(overdue),
        overdue_high_priority_count=len(overdue_high),
        by_category=by_category,
        by_priority=by_priority,
        overdue_threshold_days=settings.OVERDUE_THRESHOLD_DAYS,
    )
