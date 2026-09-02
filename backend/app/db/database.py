import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.db.base import Base
import logging

logger = logging.getLogger(__name__)

# Default to SQLite for local development
USE_POSTGRES = os.environ.get("USE_POSTGRES", "0").lower() == "1"

if USE_POSTGRES:
    # Use PostgreSQL (requires Docker)
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:password@postgres:5432/surveillance_db"
    )
    logger.info("Using PostgreSQL database")
else:
    # Use SQLite locally
    db_url = "sqlite:///./surveillance.db"
    logger.info("Using SQLite database (local development)")

try:
    engine = create_engine(
        db_url,
        echo=os.environ.get("DEBUG", "false").lower() == "true",
        pool_pre_ping=True,
        connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    # Fallback to SQLite
    db_url = "sqlite:///./surveillance.db"
    logger.warning("Falling back to SQLite database")
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database - create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
