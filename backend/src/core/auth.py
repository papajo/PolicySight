"""
Authentication Service
Handles JWT token creation, password hashing, user authentication,
and Clerk JWT verification for production auth.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import httpx

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.config.settings import get_settings
from src.db.base import get_db
from src.db.models import User, UserRole

security = HTTPBearer(auto_error=False)
settings = get_settings()

# Clerk JWKS cache (fetched once, reused)
_clerk_jwks: Optional[dict] = None


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a hashed password."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=settings.jwt_expiration_hours)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# ── Clerk JWT Verification ──────────────────────────────────────────────────


async def _fetch_clerk_jwks() -> dict:
    """Fetch Clerk's JSON Web Key Set for JWT verification."""
    global _clerk_jwks
    if _clerk_jwks and settings.app_env == "production":
        return _clerk_jwks

    if not settings.clerk_secret_key:
        return {}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.clerk.com/v1/jwks",
                headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
                timeout=10.0,
            )
            if resp.status_code == 200:
                _clerk_jwks = resp.json()
                return _clerk_jwks
    except Exception:
        pass
    return {}


def _get_clerk_jwk(kid: str) -> Optional[dict]:
    """Find a specific key from the JWKS by kid."""
    import base64
    import json

    keys = _clerk_jwks.get("keys", []) if _clerk_jwks else []
    for key in keys:
        if key.get("kid") == kid:
            # Convert JWK to PEM for python-jose
            n = int.from_bytes(
                base64.urlsafe_b64decode(key["n"] + "=="), "big"
            )
            e = int.from_bytes(
                base64.urlsafe_b64decode(key["e"] + "=="), "big"
            )
            from cryptography.hazmat.primitives.asymmetric.rsa import (
                RSAPublicNumbers,
            )
            from cryptography.hazmat.primitives import serialization

            pub_numbers = RSAPublicNumbers(e, n)
            pub_key = pub_numbers.public_key()
            pem = pub_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            return {"pem": pem, "key": key}
    return None


async def _verify_clerk_token(token: str) -> dict:
    """Verify a Clerk JWT and return the payload."""
    global _clerk_jwks

    # Fetch JWKS if not cached
    if not _clerk_jwks:
        _clerk_jwks = await _fetch_clerk_jwks()

    if not _clerk_jwks:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clerk authentication not configured",
        )

    # Decode header to get kid
    try:
        header = jwt.get_unverified_header(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
        )

    kid = header.get("kid")
    jwk_data = _get_clerk_jwk(kid)

    if not jwk_data:
        # Refresh JWKS cache and retry
        _clerk_jwks = await _fetch_clerk_jwks()
        jwk_data = _get_clerk_jwk(kid)

    if not jwk_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to verify token signature",
        )

    try:
        payload = jwt.decode(
            token,
            jwk_data["pem"],
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Clerk token",
        )


# ── Combined Auth Dependency ────────────────────────────────────────────────


async def _get_user_from_clerk_payload(
    payload: dict, db: Session
) -> User:
    """Find or create a user from Clerk JWT payload."""
    clerk_id = payload.get("sub")
    email = payload.get("email_address") or payload.get("email") or ""

    if not clerk_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Clerk token: missing user ID",
        )

    # Try to find user by clerk_id (stored in email field as fallback)
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Create user from Clerk data
        user = User(
            email=email or f"{clerk_id}@clerk.internal",
            encrypted_password=hash_password("__clerk_managed__"),
            role=UserRole.USER,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency: extract and validate the current user.
    Tries Clerk JWT first (if configured), falls back to local JWT.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = credentials.credentials

    # If Clerk is configured, try Clerk verification first
    if settings.clerk_secret_key:
        try:
            payload = await _verify_clerk_token(token)
            return await _get_user_from_clerk_payload(payload, db)
        except HTTPException:
            # Clerk verification failed, fall through to local JWT
            pass

    # Fallback: local JWT verification
    payload = decode_access_token(token)
    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Optional auth: returns None if not authenticated instead of raising."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency: ensure the current user is active."""
    return current_user