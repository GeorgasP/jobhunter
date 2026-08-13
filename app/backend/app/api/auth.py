"""
Authentication dependency για FastAPI routes.
Verifies Clerk JWT and returns User from DB (auto-creates on first sign-in).
"""
import logging
from typing import Annotated

import httpx
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.db.models import User, Tier
from app.db.session import get_db

log = logging.getLogger(__name__)

# Cache Clerk JWKs (24h TTL)
_jwks_cache = {"keys": None, "fetched_at": 0}


async def _get_clerk_jwks() -> dict:
    """Fetch Clerk's public JWKs for JWT verification."""
    import time
    if _jwks_cache["keys"] and (time.time() - _jwks_cache["fetched_at"] < 86400):
        return _jwks_cache["keys"]

    # Clerk JWKs URL pattern
    if not settings.CLERK_PUBLIC_KEY:
        raise RuntimeError("CLERK_PUBLIC_KEY not configured")

    # In production, fetch from https://<your-clerk-instance>/.well-known/jwks.json
    # For dev, use the static public key
    async with httpx.AsyncClient() as client:
        # Stub for now — replace with actual Clerk instance URL
        url = f"{settings.CLERK_PUBLIC_KEY}/.well-known/jwks.json"
        try:
            r = await client.get(url, timeout=5.0)
            r.raise_for_status()
            jwks = r.json()
            _jwks_cache["keys"] = jwks
            _jwks_cache["fetched_at"] = time.time()
            return jwks
        except Exception as e:
            log.warning(f"Failed to fetch Clerk JWKs: {e}")
            return {"keys": []}


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency. Verifies Bearer JWT from Clerk, returns User.
    Auto-creates user in DB on first login.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = authorization.removeprefix("Bearer ")

    # Verify JWT (signature + expiry)
    try:
        # Decode without verification for now (dev mode)
        # In production: verify against Clerk JWKs
        if settings.ENVIRONMENT == "development":
            payload = jwt.get_unverified_claims(token)
        else:
            jwks = await _get_clerk_jwks()
            payload = jwt.decode(
                token, jwks, algorithms=["RS256"],
                options={"verify_aud": False},
            )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )

    clerk_id = payload.get("sub")
    email = payload.get("email")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Token missing sub claim")

    # Find or create user
    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            clerk_id=clerk_id,
            email=email or f"{clerk_id}@unknown.local",
            name=payload.get("name"),
            tier=Tier.FREE,
            preferences={},
        )
        db.add(user)
        await db.flush()  # get the ID

    return user


# Type alias για convenience στα route handlers
CurrentUser = Annotated[User, Depends(get_current_user)]
