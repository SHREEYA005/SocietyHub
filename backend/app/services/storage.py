"""
Local filesystem storage abstraction for complaint photos.

Kept intentionally simple (no extra dependency) but isolated behind a small
interface so swapping to S3 / Cloudinary / etc. later only touches this file.
Never trusts the client-provided filename: a new UUID-based name is always
generated, and the original extension is validated against an allow-list.
"""
import os
import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException, status

from app.config import get_settings

settings = get_settings()

_EXT_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _upload_dir() -> Path:
    path = Path(settings.UPLOAD_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


async def save_complaint_photo(file: UploadFile) -> str:
    """Validates and persists an uploaded complaint photo.

    Returns the relative path (as stored in the DB) on success.
    Raises HTTPException(400) on any validation failure.
    """
    if file.content_type not in settings.allowed_image_types_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file.content_type}'. "
                   f"Allowed types: {', '.join(settings.allowed_image_types_list)}.",
        )

    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File is too large. Maximum allowed size is {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )
    if len(contents) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    ext = _EXT_BY_MIME.get(file.content_type, "")
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest = _upload_dir() / safe_name

    try:
        with open(dest, "wb") as f:
            f.write(contents)
    except OSError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the uploaded file. Please try again.",
        )

    return f"{settings.UPLOAD_DIR}/{safe_name}"


def photo_exists(photo_path: str | None) -> bool:
    if not photo_path:
        return False
    return os.path.isfile(photo_path)
