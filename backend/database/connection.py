# database/connection.py
#
# RESPONSIBILITY: Database connection setup.
# Creates the SQLAlchemy engine and session factory.
#
# WHY SessionLocal?
# Each request gets its own database session.
# Session opens → request runs → session closes.
# This prevents connection leaks.

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import DATABASE_URL

# Engine = actual connection to PostgreSQL
engine = create_engine(DATABASE_URL)

# SessionLocal = factory that creates database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base = parent class for all your models
# Every table class inherits from this
Base = declarative_base()


def get_db():
    """
    Dependency function for FastAPI.
    Yields a database session for each request.
    Automatically closes it when request is done.

    Usage in routes:
        def my_endpoint(db: Session = Depends(get_db)):
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()