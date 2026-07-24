# core/dependencies.py
#
# RESPONSIBILITY: FastAPI dependency functions.
# These are injected into route functions via Depends().
#
# get_current_user = extracts and validates user from JWT token
# This is what makes routes "protected"

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import User
from services.auth_service import verify_token, get_user_by_id

# HTTPBearer extracts "Bearer <token>" from Authorization header
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that protects routes.

    Extracts JWT from Authorization header
    Verifies the signature
    Looks up the user in database
    Returns the User object

    If anything fails → raises 401 Unauthorized automatically

    Usage:
        @router.get("/protected")
        def my_route(current_user: User = Depends(get_current_user)):
            return {"user": current_user.email}
    """

    # This error is returned if token is missing or invalid
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Extract and verify the token
    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise credentials_exception

    # Get user_id from token payload
    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Look up user in database
    user = get_user_by_id(db, user_id=int(user_id))
    if user is None:
        raise credentials_exception

    # Check user is still active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated."
        )

    return user


def get_optional_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(
        HTTPBearer(auto_error=False)
    )
) -> User | None:
    """
    Optional version — returns user if logged in, None if not.
    Use for routes that work both logged in and anonymous.
    """
    if credentials is None:
        return None
    try:
        return get_current_user(credentials=credentials, db=db)
    except HTTPException:
        return None