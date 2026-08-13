"""
JobHunter Backend — FastAPI entry point
========================================
Production-grade async API server για το JobHunter SaaS.

Endpoints overview:
  /api/me              → current user
  /api/cvs             → CV management
  /api/jobs/today      → daily matches
  /api/cover-letters   → AI generation
  /api/applications    → tracking
  /api/stripe/*        → payments

Run locally:
  uvicorn app.main:app --reload --port 8000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.session import init_db, close_db
from app.api import users, cvs, jobs, cover_letters, applications, stripe_routes

# ════════════════════════════════════════════════════════════════
# Lifecycle
# ════════════════════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup + shutdown hooks."""
    logging.info("🚀 JobHunter backend starting...")
    await init_db()
    yield
    logging.info("🛑 JobHunter backend shutting down...")
    await close_db()


# ════════════════════════════════════════════════════════════════
# App initialization
# ════════════════════════════════════════════════════════════════
app = FastAPI(
    title="JobHunter API",
    version="0.1.0",
    description="AI-powered job scouting + application automation",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url=None,
)

# CORS — frontend domain only
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)


# ════════════════════════════════════════════════════════════════
# Health check
# ════════════════════════════════════════════════════════════════
@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
async def root():
    return {
        "service": "JobHunter API",
        "docs": "/docs",
        "health": "/health",
    }


# ════════════════════════════════════════════════════════════════
# Routers
# ════════════════════════════════════════════════════════════════
app.include_router(users.router, prefix="/api/me", tags=["users"])
app.include_router(cvs.router, prefix="/api/cvs", tags=["cvs"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(cover_letters.router, prefix="/api/cover-letters", tags=["cover_letters"])
app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
app.include_router(stripe_routes.router, prefix="/api/stripe", tags=["stripe"])


# ════════════════════════════════════════════════════════════════
# Global exception handler
# ════════════════════════════════════════════════════════════════
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler. Sends to Sentry in production."""
    logging.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": str(exc)},
    )
