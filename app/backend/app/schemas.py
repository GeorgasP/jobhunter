"""
Pydantic schemas για API requests/responses.
Single file — keeps it greppable.
"""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.db.models import Tier, MatchStatus, ApplicationStatus


# ════════════════════════════════════════════════════════════════
# USERS
# ════════════════════════════════════════════════════════════════
class UserPreferences(BaseModel):
    """Job matching preferences."""
    locations: list[str] = Field(default_factory=list, description="Madrid, Athens, Remote EU...")
    salary_min: int | None = None
    salary_max: int | None = None
    languages: list[str] = Field(default_factory=lambda: ["en"])  # CV languages
    roles: list[str] = Field(default_factory=list, description="Customer Success, BD, PM...")
    industries: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    experience_level: Literal["entry", "mid", "senior"] = "entry"
    remote_only: bool = False
    willing_to_relocate: bool = True


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    name: str | None
    tier: Tier
    preferences: UserPreferences
    created_at: datetime

    class Config:
        from_attributes = True


class PreferencesUpdate(BaseModel):
    """PATCH /api/me/preferences body."""
    locations: list[str] | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    languages: list[str] | None = None
    roles: list[str] | None = None
    industries: list[str] | None = None
    exclude_keywords: list[str] | None = None
    experience_level: Literal["entry", "mid", "senior"] | None = None
    remote_only: bool | None = None
    willing_to_relocate: bool | None = None


# ════════════════════════════════════════════════════════════════
# CVs
# ════════════════════════════════════════════════════════════════
class CVResponse(BaseModel):
    id: UUID
    name: str
    language: str
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ════════════════════════════════════════════════════════════════
# JOBS
# ════════════════════════════════════════════════════════════════
class JobResponse(BaseModel):
    id: UUID
    company: str
    title: str
    location: str | None
    description: str | None
    url: str
    salary_min: int | None
    salary_max: int | None
    remote: bool
    posted_at: datetime | None

    class Config:
        from_attributes = True


class JobMatchResponse(BaseModel):
    id: UUID
    job: JobResponse
    relevance_score: int
    match_reasons: dict
    status: MatchStatus
    created_at: datetime

    class Config:
        from_attributes = True


# ════════════════════════════════════════════════════════════════
# COVER LETTERS
# ════════════════════════════════════════════════════════════════
class GenerateCoverLetterRequest(BaseModel):
    match_id: UUID
    cv_id: UUID | None = None  # uses primary CV if not specified
    language: Literal["en", "el", "es", "de", "fr"] = "en"
    tone: Literal["professional", "warm", "confident"] = "professional"
    additional_notes: str | None = Field(None, max_length=500)


class CoverLetterResponse(BaseModel):
    id: UUID
    match_id: UUID
    language: str
    content: str
    generated_at: datetime

    class Config:
        from_attributes = True


# ════════════════════════════════════════════════════════════════
# APPLICATIONS
# ════════════════════════════════════════════════════════════════
class CreateApplicationRequest(BaseModel):
    match_id: UUID
    cover_letter_id: UUID | None = None
    method: Literal["one_click", "manual", "auto"] = "manual"
    notes: str | None = Field(None, max_length=2000)


class ApplicationResponse(BaseModel):
    id: UUID
    job: JobResponse
    applied_at: datetime
    method: str | None
    status: ApplicationStatus
    response_received_at: datetime | None
    notes: str | None

    class Config:
        from_attributes = True


# ════════════════════════════════════════════════════════════════
# STRIPE / BILLING
# ════════════════════════════════════════════════════════════════
class CheckoutSessionRequest(BaseModel):
    tier: Literal["pro", "premium"]
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    url: str
    session_id: str


class BillingPortalResponse(BaseModel):
    url: str
