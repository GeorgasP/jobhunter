"""
/api/cvs — CV upload + management.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import CurrentUser
from app.db.models import CV
from app.db.session import get_db
from app.schemas import CVResponse
from app.ai.cover_letter import parse_cv_text

router = APIRouter()
log = logging.getLogger(__name__)

ALLOWED_TYPES = {"application/pdf", "application/octet-stream"}
MAX_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("", response_model=CVResponse, status_code=201)
async def upload_cv(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
    name: str = Form("My CV"),
    language: str = Form("en"),
    is_primary: bool = Form(False),
):
    """Upload PDF CV. Parses text for AI use."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 5MB)")

    try:
        text = await parse_cv_text(pdf_bytes)
    except Exception as e:
        log.exception("CV parse failed")
        raise HTTPException(status_code=400, detail=f"Could not parse PDF: {e}")

    if len(text) < 100:
        raise HTTPException(
            status_code=400,
            detail="CV text too short. Make sure it's not a scanned image.",
        )

    # TODO: Upload to Supabase Storage. For now, persist text only.
    storage_url = f"users/{user.id}/cvs/{file.filename}"

    cv = CV(
        user_id=user.id,
        name=name,
        language=language,
        storage_url=storage_url,
        parsed_text=text,
        is_primary=is_primary,
    )

    # Unset other primary if this one is primary
    if is_primary:
        await db.execute(
            update(CV).where(CV.user_id == user.id).values(is_primary=False)
        )

    db.add(cv)
    await db.flush()
    return cv


@router.get("", response_model=list[CVResponse])
async def list_cvs(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    """List user's CVs."""
    q = select(CV).where(CV.user_id == user.id).order_by(CV.created_at.desc())
    cvs = (await db.execute(q)).scalars().all()
    return list(cvs)


@router.delete("/{cv_id}", status_code=204)
async def delete_cv(cv_id: UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    """Delete a CV."""
    q = select(CV).where(CV.id == cv_id, CV.user_id == user.id)
    cv = (await db.execute(q)).scalar_one_or_none()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    await db.delete(cv)


@router.post("/{cv_id}/primary", response_model=CVResponse)
async def set_primary(cv_id: UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    """Mark a CV as primary (used by default for cover letters)."""
    q = select(CV).where(CV.id == cv_id, CV.user_id == user.id)
    cv = (await db.execute(q)).scalar_one_or_none()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    await db.execute(
        update(CV).where(CV.user_id == user.id).values(is_primary=False)
    )
    cv.is_primary = True
    await db.flush()
    return cv
