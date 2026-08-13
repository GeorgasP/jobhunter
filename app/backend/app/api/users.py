"""
/api/me — current user endpoints.
"""
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.api.auth import CurrentUser
from app.db.session import get_db
from app.schemas import UserResponse, UserPreferences, PreferencesUpdate

router = APIRouter()


@router.get("", response_model=UserResponse)
async def get_me(user: CurrentUser):
    """Returns the authenticated user's profile + preferences."""
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        tier=user.tier,
        preferences=UserPreferences(**(user.preferences or {})),
        created_at=user.created_at,
    )


@router.patch("/preferences", response_model=UserResponse)
async def update_preferences(
    update: PreferencesUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Update job matching preferences. Only fields provided are changed."""
    current = user.preferences or {}
    for field, value in update.model_dump(exclude_none=True).items():
        current[field] = value
    user.preferences = current
    await db.flush()

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        tier=user.tier,
        preferences=UserPreferences(**current),
        created_at=user.created_at,
    )
