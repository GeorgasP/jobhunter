"""
SQLAlchemy ORM models — JobHunter database schema.
Mirror του ARCHITECTURE.md schema. Production-ready με indexes.
"""
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index, Integer,
    JSON, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Tier(StrEnum):
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class MatchStatus(StrEnum):
    PENDING = "pending"        # Not yet acted on
    SAVED = "saved"            # User saved for later
    APPLIED = "applied"        # User applied
    IGNORED = "ignored"        # User dismissed
    REJECTED = "rejected"      # Company rejected


class ApplicationStatus(StrEnum):
    SENT = "sent"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEWING = "interviewing"
    REJECTED = "rejected"
    GHOSTED = "ghosted"
    OFFER = "offer"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


# ════════════════════════════════════════════════════════════════
# Users
# ════════════════════════════════════════════════════════════════
class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PgUUID, primary_key=True, default=uuid4)
    clerk_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    tier: Mapped[Tier] = mapped_column(String(20), default=Tier.FREE, nullable=False)

    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), unique=True)

    # JSONB για user preferences (locations, salary range, languages, etc.)
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False,
    )

    # Relationships
    cvs: Mapped[list["CV"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    matches: Mapped[list["JobMatch"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    applications: Mapped[list["Application"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")


# ════════════════════════════════════════════════════════════════
# CVs
# ════════════════════════════════════════════════════════════════
class CV(Base):
    __tablename__ = "cvs"

    id: Mapped[UUID] = mapped_column(PgUUID, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PgUUID, ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(5), nullable=False)  # 'en', 'el', 'es'...
    storage_url: Mapped[str] = mapped_column(Text, nullable=False)    # Supabase Storage path
    parsed_text: Mapped[str | None] = mapped_column(Text)             # Extracted text για AI
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="cvs")


# ════════════════════════════════════════════════════════════════
# Jobs (discovered by scrapers)
# ════════════════════════════════════════════════════════════════
class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_jobs_source_external"),
        Index("ix_jobs_company", "company"),
        Index("ix_jobs_location", "location"),
        Index("ix_jobs_posted_at", "posted_at"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID, primary_key=True, default=uuid4)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)

    company: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text, nullable=False)

    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    remote: Mapped[bool] = mapped_column(Boolean, default=False)

    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    raw_data: Mapped[dict | None] = mapped_column(JSONB)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    matches: Mapped[list["JobMatch"]] = relationship(back_populates="job", cascade="all, delete-orphan")


# ════════════════════════════════════════════════════════════════
# User → Job matches (computed daily)
# ════════════════════════════════════════════════════════════════
class JobMatch(Base):
    __tablename__ = "job_matches"
    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_matches_user_job"),
        Index("ix_matches_user_score", "user_id", "relevance_score"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PgUUID, ForeignKey("users.id", ondelete="CASCADE"))
    job_id: Mapped[UUID] = mapped_column(PgUUID, ForeignKey("jobs.id", ondelete="CASCADE"))

    relevance_score: Mapped[int] = mapped_column(Integer, nullable=False)
    match_reasons: Mapped[dict] = mapped_column(JSONB, default=dict)

    status: Mapped[MatchStatus] = mapped_column(String(20), default=MatchStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="matches")
    job: Mapped[Job] = relationship(back_populates="matches")
    cover_letters: Mapped[list["CoverLetter"]] = relationship(back_populates="match", cascade="all, delete-orphan")


# ════════════════════════════════════════════════════════════════
# Cover letters
# ════════════════════════════════════════════════════════════════
class CoverLetter(Base):
    __tablename__ = "cover_letters"

    id: Mapped[UUID] = mapped_column(PgUUID, primary_key=True, default=uuid4)
    match_id: Mapped[UUID] = mapped_column(PgUUID, ForeignKey("job_matches.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(PgUUID, ForeignKey("users.id", ondelete="CASCADE"))

    language: Mapped[str] = mapped_column(String(5), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    ai_model: Mapped[str | None] = mapped_column(String(50))
    tokens_used: Mapped[int | None] = mapped_column(Integer)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    match: Mapped[JobMatch] = relationship(back_populates="cover_letters")


# ════════════════════════════════════════════════════════════════
# Applications (tracking what user applied to)
# ════════════════════════════════════════════════════════════════
class Application(Base):
    __tablename__ = "applications"

    id: Mapped[UUID] = mapped_column(PgUUID, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PgUUID, ForeignKey("users.id", ondelete="CASCADE"))
    job_id: Mapped[UUID] = mapped_column(PgUUID, ForeignKey("jobs.id", ondelete="CASCADE"))
    match_id: Mapped[UUID | None] = mapped_column(PgUUID, ForeignKey("job_matches.id"))
    cover_letter_id: Mapped[UUID | None] = mapped_column(PgUUID, ForeignKey("cover_letters.id"))

    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    method: Mapped[str | None] = mapped_column(String(20))    # 'one_click' | 'manual' | 'auto'
    status: Mapped[ApplicationStatus] = mapped_column(String(30), default=ApplicationStatus.SENT)
    response_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_status: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="applications")


# ════════════════════════════════════════════════════════════════
# Subscriptions (Stripe state mirror)
# ════════════════════════════════════════════════════════════════
class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[UUID] = mapped_column(PgUUID, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PgUUID, ForeignKey("users.id", ondelete="CASCADE"))
    stripe_subscription_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    tier: Mapped[Tier] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(50))    # active/canceled/past_due/trialing
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="subscriptions")
