# api/routes/auth.py
#
# RESPONSIBILITY: Authentication endpoints
#   POST /auth/register → create new account
#   POST /auth/login    → get JWT token
#   GET  /auth/me       → get current user info

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, EmailStr
from datetime import timedelta
from database.connection import get_db
from database.models import User
from services.auth_service import (
    get_user_by_email,
    create_user,
    authenticate_user,
    create_access_token
)
from core.dependencies import get_current_user
from core.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr                    # auto-validates email format
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    full_name: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/auth/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account"
)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Creates a new user account and returns a JWT token.
    User is automatically logged in after registration.
    """

    # Check email not already taken
    existing = get_user_by_email(db, request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    # Create user — password gets hashed inside create_user()
    user = create_user(
        db=db,
        email=request.email,
        full_name=request.full_name,
        password=request.password
    )

    # Generate JWT token — user is logged in immediately
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name
    }


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Login to your account"
)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Verifies email + password and returns a JWT token.
    Include this token in subsequent requests as:
    Authorization: Bearer <token>
    """

    # Verify credentials
    user = authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name
    }


@router.get(
    "/auth/me",
    response_model=UserResponse,
    summary="Get current user info"
)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns info about the currently logged-in user.
    Requires valid JWT token in Authorization header.
    """
    return current_user