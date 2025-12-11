"""
Database Connection and Session Management
Handles SQLAlchemy setup with Supabase PostgreSQL
"""

from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

# Base class for models (can be imported without database connection)
Base = declarative_base()

# Lazy-initialized engine and session
_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def get_engine() -> Engine:
    """
    Get or create the SQLAlchemy engine.
    Uses lazy initialization to avoid errors during import when DATABASE_URL is not set.
    """
    global _engine
    if _engine is None:
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL is not configured. " "Please set the DATABASE_URL environment variable.")
        _engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=10,
            max_overflow=20,
            echo=settings.DEBUG,  # Log SQL queries in debug mode
        )
    return _engine


def get_session_local() -> sessionmaker:
    """Get or create the SessionLocal factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Yields a session and ensures it's closed after use.

    Usage in FastAPI:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables.
    This is called during application startup.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
