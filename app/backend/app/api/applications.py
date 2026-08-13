"""
/api/applications — tracking what user applied to.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.auth import CurrentUser
from app.db.models import Application, Job, JobMatch, MatchStatus
from app.db.session import get_db
from app.schemas import ApplicationResponse, CreateApplicationRequest, JobResponse

router = APIRouter()


@router.post("", response_model=ApplicationResponse, status_code=201)
async def create_application(
    req: CreateApplicationRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Mark a job match as applied. Tracks for analytics + follow-up."""
    q = (
        select(JobMatch)
        .options(selectinload(JobMatch.job))
        .where(JobMatch.id == req.match_id, JobMatch.user_id == user.id)
    )
    match = (await db.execute(q)).scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    application = Application(
        user_id=user.id,
        job_id=match.job_id,
        match_id=match.id,
        cover_letter_id=req.cover_letter_id,
        method=req.method,
        notes=req.notes,
    )

    match.status = MatchStatus.APPLIED
    db.add(application)
    await db.flush()

    return ApplicationResponse(
        id=application.id,
        job=JobResponse.model_validate(match.job),
        applied_at=application.applied_at,
        method=application.method,
        status=application.status,
        response_received_at=application.response_received_at,
        notes=application.notes,
    )


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    """List all applications με their current status."""
    # Join with job to populate the response
    q = (
        select(Application, Job)
        .join(Job, Application.job_id == Job.id)
        .where(Application.user_id == user.id)
        .order_by(Application.applied_at.desc())
    )
    rows = (await db.execute(q)).all()

    return [
        ApplicationResponse(
            id=app.id,
            job=JobResponse.model_validate(job),
            applied_at=app.applied_at,
            method=app.method,
            status=app.status,
            response_received_at=app.response_received_at,
            notes=app.notes,
        )
        for app, job in rows
    ]
