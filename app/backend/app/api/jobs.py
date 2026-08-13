"""
/api/jobs — daily job matches per user.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.auth import CurrentUser
from app.config import settings
from app.db.models import JobMatch, MatchStatus, Tier
from app.db.session import get_db
from app.schemas import JobMatchResponse, JobResponse

router = APIRouter()


def _daily_limit(tier: Tier) -> int:
    return {
        Tier.FREE: settings.FREE_TIER_JOBS_PER_DAY,
        Tier.PRO: settings.PRO_TIER_JOBS_PER_DAY,
        Tier.PREMIUM: settings.PREMIUM_TIER_JOBS_PER_DAY,
        Tier.ENTERPRISE: 999,
    }.get(tier, 10)


@router.get("/today", response_model=list[JobMatchResponse])
async def get_today_matches(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int | None = None,
):
    """
    Returns today's job matches, scored και filtered per user preferences.

    Limit defaults to tier's daily limit. Cannot exceed it.
    """
    actual_limit = min(limit or _daily_limit(user.tier), _daily_limit(user.tier))

    yesterday = datetime.now(timezone.utc) - timedelta(days=1)

    query = (
        select(JobMatch)
        .options(selectinload(JobMatch.job))
        .where(
            JobMatch.user_id == user.id,
            JobMatch.created_at >= yesterday,
            JobMatch.status == MatchStatus.PENDING,
        )
        .order_by(JobMatch.relevance_score.desc())
        .limit(actual_limit)
    )

    matches = (await db.execute(query)).scalars().all()
    return [
        JobMatchResponse(
            id=m.id,
            job=JobResponse.model_validate(m.job),
            relevance_score=m.relevance_score,
            match_reasons=m.match_reasons,
            status=m.status,
            created_at=m.created_at,
        )
        for m in matches
    ]


@router.get("/{match_id}", response_model=JobMatchResponse)
async def get_match(
    match_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Single match detail (full job description)."""
    q = (
        select(JobMatch)
        .options(selectinload(JobMatch.job))
        .where(JobMatch.id == match_id, JobMatch.user_id == user.id)
    )
    match = (await db.execute(q)).scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    return JobMatchResponse(
        id=match.id,
        job=JobResponse.model_validate(match.job),
        relevance_score=match.relevance_score,
        match_reasons=match.match_reasons,
        status=match.status,
        created_at=match.created_at,
    )


@router.post("/{match_id}/save", response_model=JobMatchResponse)
async def save_match(
    match_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Save a match για later review."""
    q = select(JobMatch).where(
        JobMatch.id == match_id, JobMatch.user_id == user.id,
    )
    match = (await db.execute(q)).scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    match.status = MatchStatus.SAVED
    await db.flush()
    return JobMatchResponse.model_validate(match)


@router.post("/{match_id}/ignore", response_model=JobMatchResponse)
async def ignore_match(
    match_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Hide a match. Won't show again."""
    q = select(JobMatch).where(
        JobMatch.id == match_id, JobMatch.user_id == user.id,
    )
    match = (await db.execute(q)).scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    match.status = MatchStatus.IGNORED
    await db.flush()
    return JobMatchResponse.model_validate(match)
