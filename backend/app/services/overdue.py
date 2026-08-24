"""
Overdue detection.

Deliberately NOT stored as a column on Complaint - it is computed on read
from `created_at`, `status` and the configurable OVERDUE_THRESHOLD_DAYS
setting. This guarantees overdue status is always consistent with the
current threshold, even if the threshold is changed later, and it means a
RESOLVED complaint can never be "stuck" showing as overdue.
"""
from datetime import datetime

from app.config import get_settings
from app.models import Complaint, ComplaintStatus

settings = get_settings()


def is_overdue(complaint: Complaint, threshold_days: int | None = None) -> bool:
    if complaint.status == ComplaintStatus.RESOLVED:
        return False
    threshold = threshold_days if threshold_days is not None else settings.OVERDUE_THRESHOLD_DAYS
    age = datetime.utcnow() - complaint.created_at
    return age.days >= threshold


def days_open(complaint: Complaint) -> int:
    end = complaint.resolved_at or datetime.utcnow()
    return max((end - complaint.created_at).days, 0)


def sla_message(complaint: Complaint, threshold_days: int | None = None) -> str:
    """Human readable SLA line, e.g. 'Due in 18 hours' or 'Overdue by 2 days'."""
    if complaint.status == ComplaintStatus.RESOLVED:
        return "Resolved"

    threshold = threshold_days if threshold_days is not None else settings.OVERDUE_THRESHOLD_DAYS
    deadline = complaint.created_at.timestamp() + threshold * 86400
    remaining_seconds = deadline - datetime.utcnow().timestamp()

    if remaining_seconds >= 0:
        hours = int(remaining_seconds // 3600)
        if hours < 1:
            return "Due within the hour"
        if hours < 24:
            return f"Due in {hours} hour{'s' if hours != 1 else ''}"
        days = hours // 24
        return f"Due in {days} day{'s' if days != 1 else ''}"
    else:
        overdue_days = int(abs(remaining_seconds) // 86400)
        if overdue_days < 1:
            return "Overdue by less than a day"
        return f"Overdue by {overdue_days} day{'s' if overdue_days != 1 else ''}"
