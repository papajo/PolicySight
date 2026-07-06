"""
Authentication API Routes
Handles user registration, login, token refresh, and Clerk JWT exchange.
Local JWT works for development; Clerk handles production auth.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.db.models import User, UserRole
from src.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    _verify_clerk_token,
    _get_user_from_clerk_payload,
)
from src.config.settings import get_settings

router = APIRouter()
settings = get_settings()


class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str = "user"


class LoginRequest(BaseModel):
    email: str
    password: str


class ClerkSessionRequest(BaseModel):
    """Sent by the frontend after Clerk completes sign-in.
    The frontend calls Clerk's `getSession()` and passes the JWT here
    so the backend can issue its own access token."""
    clerk_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    role: str


class UserResponse(BaseModel):
    id: int
    email: str
    role: str


# ── Local Auth (development fallback) ──────────────────────────────────────


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account (local auth — development only)."""
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    if request.role not in ("user", "agent"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'user' or 'agent'.",
        )

    user = User(
        email=request.email,
        encrypted_password=hash_password(request.password),
        role=UserRole.AGENT if request.role == "agent" else UserRole.USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": user.id, "role": user.role.value})

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        role=user.role.value,
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password (local auth — development only)."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.encrypted_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(data={"sub": user.id, "role": user.role.value})

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        role=user.role.value,
    )


# ── Clerk Auth (production) ────────────────────────────────────────────────


@router.post("/clerk-session", response_model=TokenResponse)
async def clerk_session_exchange(
    request: ClerkSessionRequest,
    db: Session = Depends(get_db),
):
    """
    Exchange a Clerk frontend JWT for a PolicySight access token.
    Call this from the frontend after Clerk's signIn() or signUp() completes:
      const { session } = await clerkClient.signIn()
      const res = await fetch('/api/auth/clerk-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clerk_token: session.id })
      })
      localStorage.setItem('token', res.access_token)
    """
    if not settings.clerk_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clerk authentication is not configured. Set CLERK_SECRET_KEY in .env",
        )

    try:
        payload = await _verify_clerk_token(request.clerk_token)
        user = await _get_user_from_clerk_payload(payload, db)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Clerk token",
        ) from exc

    # Issue our own JWT that subsequent requests will use
    token = create_access_token(data={"sub": user.id, "role": user.role.value})

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        role=user.role.value,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user's profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
    )
