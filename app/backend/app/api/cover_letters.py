"""
/api/cover-letters — AI-generated cover letters per job match.
"""
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.auth import CurrentUser
from app.config import settings
from app.db.models import CV, CoverLetter, JobMatch, Tier
from app.db.session import get_db
from app.schemas import CoverLetterResponse, GenerateCoverLetterRequest
from app.ai.cover_letter import generate_cover_letter

router = APIRouter()
log = logging.getLogger(__name__)


def _daily_limit(tier: Tier) -> int:
    return {
        Tier.FREE: 0,    # FREE tier doesn't get AI cover letters
        Tier.PRO: settings.PRO_TIER_COVER_LETTERS_PER_DAY,
        Tier.PREMIUM: settings.PREMIUM_TIER_COVER_LETTERS_PER_DAY,
        Tier.ENTERPRISE: 999,
    }.get(tier, 0)


@router.post("/generate", response_model=CoverLetterResponse, status_code=201)
async def generate(
    req: GenerateCoverLetterRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate AI cover letter for a job match. Requires Pro tier or above.
    Rate limited per user tier.
    """
    # Tier check
    if user.tier == Tier.FREE:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="AI cover letters require Pro or Premium tier",
        )

    # Daily limit check
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0,
    )
    count_query = select(func.count(CoverLetter.id)).where(
        CoverLetter.user_id == user.id,
        CoverLetter.generated_at >= today_start,
    )
    used_today = (await db.execute(count_query)).scalar() or 0
    limit = _daily_limit(user.tier)
    if used_today >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily limit reached ({used_today}/{limit}). Upgrade tier or try tomorrow.",
        )

    # Fetch the job match (with job)
    match_query = (
        select(JobMatch)
        .options(selectinload(JobMatch.job))
        .where(JobMatch.id == req.match_id, JobMatch.user_id == user.id)
    )
    match = (await db.execute(match_query)).scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Job match not found")

    # Fetch CV
    cv_query = select(CV).where(CV.user_id == user.id)
    if req.cv_id:
        cv_query = cv_query.where(CV.id == req.cv_id)
    else:
        cv_query = cv_query.where(CV.is_primary == True)  # noqa: E712
    cv = (await db.execute(cv_query)).scalar_one_or_none()
    if not cv or not cv.parsed_text:
        raise HTTPException(
            status_code=400,
            detail="No CV found. Upload a CV first via /api/cvs.",
        )

    # Generate via Claude
    try:
        content, tokens = await generate_cover_letter(
            cv_text=cv.parsed_text,
            job_company=match.job.company,
            job_title=match.job.title,
            job_description=match.job.description or match.job.title,
            language=req.language,
            tone=req.tone,
            additional_notes=req.additional_notes,
        )
    except Exception as e:
        log.exception("Cover letter generation failed")
        raise HTTPException(status_code=502, detail=f"AI service error: {str(e)[:200]}")

    # Persist
    letter = CoverLetter(
        match_id=match.id,
        user_id=user.id,
        language=req.language,
        content=content,
        ai_model=settings.CLAUDE_MODEL_DEFAULT,
        tokens_used=tokens,
    )
    db.add(letter)
    await db.flush()

    return CoverLetterResponse(
        id=letter.id,
        match_id=letter.match_id,
        language=letter.language,
        content=letter.content,
        generated_at=letter.generated_at,
    )


@router.get("/{letter_id}", response_model=CoverLetterResponse)
async def get_cover_letter(
    letter_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Fetch a previously generated cover letter."""
    q = select(CoverLetter).where(
        CoverLetter.id == letter_id, CoverLetter.user_id == user.id,
    )
    letter = (await db.execute(q)).scalar_one_or_none()
    if not letter:
        raise HTTPException(status_code=404, detail="Cover letter not found")
    return letter
