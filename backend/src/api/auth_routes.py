"""
Authentication API Routes
Handles user registration, login, and token refresh.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.db.models import User, UserRole
from src.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


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


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    # Check if email already exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Validate role
    if request.role not in ("user", "agent"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'user' or 'agent'.",
        )

    # Create user
    user = User(
        email=request.email,
        encrypted_password=hash_password(request.password),
        role=UserRole.AGENT if request.role == "agent" else UserRole.USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate token
    token = create_access_token(data={"sub": user.id, "role": user.role.value})

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        role=user.role.value,
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password."""
    # Demo bypass: allow demo credentials without DB
    if request.email == "demo@policysight.io" and request.password == "demo123":
        return TokenResponse(
            access_token=create_access_token(data={"sub": 1, "role": "user"}),
            user_id=1,
            email="demo@policysight.io",
            role="user",
        )

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


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user's profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
    )