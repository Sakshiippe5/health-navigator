# services/auth_service.py
#
# RESPONSIBILITY: Everything auth-related
#   - Password hashing and verification
#   - JWT token creation and verification
#   - Current user extraction from token

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database.models import User
from core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# ── Password Hashing ──────────────────────────────────────────────────────────
# CryptContext handles bcrypt hashing
# bcrypt automatically salts passwords — two hashes of same password differ
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Converts plain text password to bcrypt hash.
    Example: "mypassword123" → "$2b$12$randomsaltXXXXhash..."
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against its hash.
    Returns True if they match, False otherwise.
    Never reverses the hash — just re-hashes and compares.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Token Creation ────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a signed JWT token containing user data.

    Args:
        data: Dict to encode (usually {"sub": user_id})
        expires_delta: How long token is valid

    Returns:
        Signed JWT string like "eyJhbGci..."
    """
    to_encode = data.copy()

    # Set expiry time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    # Sign the token with our SECRET_KEY
    # Anyone with SECRET_KEY can verify it
    # Anyone without SECRET_KEY cannot forge it
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ── JWT Token Verification ────────────────────────────────────────────────────

def verify_token(token: str) -> Optional[dict]:
    """
    Verifies a JWT token and returns its payload.
    Returns None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ── Database Operations ───────────────────────────────────────────────────────

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Finds a user by email address."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Finds a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, email: str, full_name: str, password: str) -> User:
    """
    Creates a new user in the database.
    Hashes password before storing — never stores plain text.
    """
    hashed = hash_password(password)
    user = User(
        email=email,
        full_name=full_name,
        password_hash=hashed
    )
    db.add(user)
    db.commit()
    db.refresh(user)  # refresh to get the auto-generated id
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Verifies email + password combination.
    Returns User if valid, None if invalid.
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user