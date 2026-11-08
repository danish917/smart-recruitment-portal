"""Database engine, session management, and health utilities."""

import os
from pathlib import Path
from typing import Any, Dict, Generator
import psycopg
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings, ensure_resolvable_url

# Raw psycopg direct connection helper (retained for backward compatibility and raw checks)
def get_db_connection():
    """Create a raw psycopg connection to the PostgreSQL database."""
    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL is not configured in environment.")
    return psycopg.connect(ensure_resolvable_url(settings.DATABASE_URL))


# SQLAlchemy Engine & Session
sqlalchemy_url = settings.sqlalchemy_database_url
engine = (
    create_engine(
        sqlalchemy_url,
        pool_pre_ping=True,
        pool_recycle=300,
    )
    if sqlalchemy_url
    else None
)

SessionLocal = (
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
    if engine
    else None
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to yield an isolated database session."""
    if not SessionLocal:
        raise RuntimeError("Database engine is not initialized.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health() -> Dict[str, Any]:
    """Perform a lightweight, safe health check against Neon PostgreSQL."""
    if not settings.DATABASE_URL:
        return {
            "status": "unconfigured",
            "message": "DATABASE_URL is not set",
        }
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database(), current_user, 1;")
                row = cur.fetchone()
                return {
                    "status": "connected",
                    "engine": "Neon PostgreSQL",
                    "database": row[0] if row else "unknown",
                }
    except Exception as exc:
        return {
            "status": "error",
            "engine": "Neon PostgreSQL",
            "error_type": type(exc).__name__,
        }
