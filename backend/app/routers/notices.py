from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models import Notice, User
from app.schemas import NoticeCreate, NoticeOut
from app.services.email_service import send_important_notice_email

router = APIRouter(prefix="/notices", tags=["Notices"])


@router.get("", response_model=List[NoticeOut])
def list_notices(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    # Important notices pinned to the top, newest first within each group.
    notices = db.query(Notice).order_by(Notice.is_important.desc(), Notice.created_at.desc()).all()
    return notices


@router.post("", response_model=NoticeOut, status_code=status.HTTP_201_CREATED)
def create_notice(payload: NoticeCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    notice = Notice(
        title=payload.title.strip(),
        content=payload.content.strip(),
        is_important=payload.is_important,
        author_id=admin.id,
        author_name=admin.name,
    )
    db.add(notice)
    db.commit()
    db.refresh(notice)

    if notice.is_important:
        residents = db.query(User).filter(User.role == "resident").all()
        for resident in residents:
            send_important_notice_email(
                to_email=resident.email,
                resident_name=resident.name,
                title=notice.title,
                content=notice.content,
                published_at=notice.created_at.isoformat(),
            )
    return notice
