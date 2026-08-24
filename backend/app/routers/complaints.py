from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models import (
    User, UserRole, Complaint, ComplaintHistory, ComplaintStatus,
    ComplaintPriority, HistoryEventType,
)
from app.schemas import (
    ComplaintOut, ComplaintDetailOut, StatusUpdate, PriorityUpdate,
)
from app.services.storage import save_complaint_photo
from app.services.overdue import is_overdue, days_open, sla_message
from app.services.email_service import send_status_change_email
from app.config import get_settings

router = APIRouter(prefix="/complaints", tags=["Complaints"])
settings = get_settings()

# Valid forward transitions. Reopening (RESOLVED -> OPEN) is intentionally a
# separate, deliberate action (see reopen endpoint) rather than an arbitrary
# transition, so it can carry its own justification/note in the audit trail.
VALID_TRANSITIONS = {
    ComplaintStatus.OPEN: {ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED},
    ComplaintStatus.IN_PROGRESS: {ComplaintStatus.OPEN, ComplaintStatus.RESOLVED},
    ComplaintStatus.RESOLVED: set(),  # terminal; use /reopen to leave this state
}


def _to_out(c: Complaint, model_cls=ComplaintOut) -> ComplaintOut:
    data = {
        "id": c.id,
        "reference_code": c.reference_code,
        "category": c.category,
        "description": c.description,
        "photo_path": c.photo_path,
        "status": c.status,
        "priority": c.priority,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
        "resolved_at": c.resolved_at,
        "resident_id": c.resident_id,
        "resident_name": c.resident.name if c.resident else None,
        "is_overdue": is_overdue(c),
        "days_open": days_open(c),
        "sla_message": sla_message(c),
    }
    if model_cls is ComplaintDetailOut:
        data["history"] = c.history
    return model_cls(**data)


def _get_owned_or_404(complaint_id: int, user: User, db: Session) -> Complaint:
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")
    if user.role != UserRole.ADMIN and complaint.resident_id != user.id:
        # Residents must never be able to access another resident's complaint,
        # even by guessing/incrementing the numeric ID.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")
    return complaint


@router.post("", response_model=ComplaintDetailOut, status_code=status.HTTP_201_CREATED)
async def create_complaint(
    category: str = Form(..., min_length=2, max_length=60),
    description: str = Form(..., min_length=10, max_length=4000),
    photo: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    photo_path = None
    if photo is not None and photo.filename:
        photo_path = await save_complaint_photo(photo)

    complaint = Complaint(
        reference_code=Complaint.generate_reference_code(),
        resident_id=current_user.id,
        category=category.strip(),
        description=description.strip(),
        photo_path=photo_path,
        status=ComplaintStatus.OPEN,
        priority=ComplaintPriority.MEDIUM,
    )
    db.add(complaint)
    db.flush()

    db.add(ComplaintHistory(
        complaint_id=complaint.id,
        event_type=HistoryEventType.CREATED,
        new_status=ComplaintStatus.OPEN,
        new_priority=ComplaintPriority.MEDIUM,
        actor_id=current_user.id,
        actor_name=current_user.name,
        note="Complaint submitted by resident.",
    ))
    db.commit()
    db.refresh(complaint)
    return _to_out(complaint, ComplaintDetailOut)


@router.get("", response_model=List[ComplaintOut])
def list_my_complaints(
    status_filter: Optional[ComplaintStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Complaint).filter(Complaint.resident_id == current_user.id)
    if status_filter:
        query = query.filter(Complaint.status == status_filter)
    complaints = query.order_by(Complaint.created_at.desc()).all()
    return [_to_out(c) for c in complaints]


@router.get("/{complaint_id}", response_model=ComplaintDetailOut)
def get_complaint(complaint_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    complaint = _get_owned_or_404(complaint_id, current_user, db)
    return _to_out(complaint, ComplaintDetailOut)


@router.get("/{complaint_id}/history", response_model=List[dict])
def get_complaint_history(complaint_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    complaint = _get_owned_or_404(complaint_id, current_user, db)
    from app.schemas import ComplaintHistoryOut
    return [ComplaintHistoryOut.model_validate(h).model_dump() for h in complaint.history]


@router.patch("/{complaint_id}/status", response_model=ComplaintDetailOut)
def update_status(
    complaint_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    old_status = complaint.status
    new_status = payload.status

    if new_status == old_status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Complaint is already in this status.")

    allowed = VALID_TRANSITIONS.get(old_status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition complaint from {old_status.value} to {new_status.value}.",
        )

    complaint.status = new_status
    complaint.updated_at = datetime.utcnow()
    if new_status == ComplaintStatus.RESOLVED:
        complaint.resolved_at = datetime.utcnow()
    else:
        complaint.resolved_at = None

    db.add(ComplaintHistory(
        complaint_id=complaint.id,
        event_type=HistoryEventType.STATUS_CHANGE,
        previous_status=old_status,
        new_status=new_status,
        actor_id=admin.id,
        actor_name=admin.name,
        note=payload.note,
    ))
    db.commit()
    db.refresh(complaint)

    resident = complaint.resident
    if resident:
        send_status_change_email(
            to_email=resident.email,
            resident_name=resident.name,
            reference_code=complaint.reference_code,
            previous_status=old_status.value,
            new_status=new_status.value,
            note=payload.note,
        )

    return _to_out(complaint, ComplaintDetailOut)


@router.patch("/{complaint_id}/reopen", response_model=ComplaintDetailOut)
def reopen_complaint(
    complaint_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Deliberate, explicit action to move a RESOLVED complaint back to OPEN.
    Requires a note explaining why, and is logged distinctly from a normal
    status transition so it is always visible in the audit trail."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")
    if complaint.status != ComplaintStatus.RESOLVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only resolved complaints can be reopened.")
    if not payload.note or not payload.note.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A note explaining the reopen reason is required.")

    old_status = complaint.status
    complaint.status = ComplaintStatus.OPEN
    complaint.resolved_at = None
    complaint.updated_at = datetime.utcnow()

    db.add(ComplaintHistory(
        complaint_id=complaint.id,
        event_type=HistoryEventType.STATUS_CHANGE,
        previous_status=old_status,
        new_status=ComplaintStatus.OPEN,
        actor_id=admin.id,
        actor_name=admin.name,
        note=f"Reopened: {payload.note}",
    ))
    db.commit()
    db.refresh(complaint)

    resident = complaint.resident
    if resident:
        send_status_change_email(
            to_email=resident.email, resident_name=resident.name,
            reference_code=complaint.reference_code,
            previous_status=old_status.value, new_status=ComplaintStatus.OPEN.value,
            note=payload.note,
        )
    return _to_out(complaint, ComplaintDetailOut)


@router.patch("/{complaint_id}/priority", response_model=ComplaintDetailOut)
def update_priority(
    complaint_id: int,
    payload: PriorityUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    old_priority = complaint.priority
    if payload.priority == old_priority:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Complaint already has this priority.")

    complaint.priority = payload.priority
    complaint.updated_at = datetime.utcnow()

    db.add(ComplaintHistory(
        complaint_id=complaint.id,
        event_type=HistoryEventType.PRIORITY_CHANGE,
        previous_priority=old_priority,
        new_priority=payload.priority,
        actor_id=admin.id,
        actor_name=admin.name,
        note=payload.note,
    ))
    db.commit()
    db.refresh(complaint)
    return _to_out(complaint, ComplaintDetailOut)
