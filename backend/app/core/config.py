
"""Application configuration settings."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

_RESOLVED_HOSTS = {
    "c-3.ap-southeast-1.aws.neon.tech": "52.76.108.241",
    "ep-proud-scene-azh186yu-pooler.c-3.ap-southeast-1.aws.neon.tech": "52.76.108.241",
    "ep-proud-scene-azh186yu.c-3.ap-southeast-1.aws.neon.tech": "52.76.108.241",
}


def ensure_resolvable_url(url: str) -> str:
    """Ensure database URL has hostaddr fallback if local DNS resolution fails."""
    if not url or "hostaddr=" in url:
        return url

    try:
        import socket
        from urllib.parse import urlparse

        clean_scheme = (
            url.replace("postgresql+psycopg://", "http://")
            .replace("postgresql://", "http://")
            .replace("postgres://", "http://")
        )

        parsed = urlparse(clean_scheme)
        host = parsed.hostname

        if not host:
            return url

        try:
            socket.gethostbyname(host)
            return url
        except socket.gaierror:
            pass

        ip = _RESOLVED_HOSTS.get(host, "52.76.108.241")
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}hostaddr={ip}"

    except Exception:
        return url


class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Recruitment Portal API"
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    # JWT Authentication
    SECRET_KEY: str = "srp-super-secure-secret-key-phase2-production-ready-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = ""
    DATABASE_URL_UNPOOLED: str = ""

    # Qdrant Vector Database
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    QDRANT_PATH: str = "storage/qdrant_db"
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    RESUME_COLLECTION_NAME: str = "candidate_resumes"
    JOB_COLLECTION_NAME: str = "job_postings"
    EMBEDDING_DIMENSION: int = 384

    # Security & CORS
    CORS_ORIGINS: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "http://localhost:3001,"
        "http://127.0.0.1:3001"
    )

    RATE_LIMIT_ENABLED: bool = True
    MAX_LOGIN_ATTEMPTS_PER_MINUTE: int = 120
    MAX_REGISTER_ATTEMPTS_PER_MINUTE: int = 120
    MAX_UPLOADS_PER_MINUTE: int = 120

    # Resume Storage
    STORAGE_BACKEND: str = "local"  # "local" or "s3"
    RESUME_STORAGE_DIR: str = "uploads/resumes"
    S3_BUCKET_NAME: str = ""
    S3_REGION: str = "us-east-1"
    S3_ENDPOINT_URL: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list:
        """Parse comma-separated CORS origins into a list of strings."""
        if not self.CORS_ORIGINS:
            return [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3001",
            ]

        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def sqlalchemy_database_url(self) -> str:
        """Ensure connection string uses the postgresql+psycopg driver."""
        url = self.DATABASE_URL

        if not url:
            return ""

        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)

        if url.startswith("postgresql://") and not url.startswith(
            "postgresql+psycopg://"
        ):
            url = url.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1,
            )

        return ensure_resolvable_url(url)

    @property
    def migration_database_url(self) -> str:
        """Direct (unpooled) connection URL for Alembic migrations as recommended by Neon."""
        url = (
            self.DATABASE_URL_UNPOOLED
            if self.DATABASE_URL_UNPOOLED
            else self.DATABASE_URL
        )

        if not url:
            return ""

        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)

        if url.startswith("postgresql://") and not url.startswith(
            "postgresql+psycopg://"
        ):
            url = url.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1,
            )

        return ensure_resolvable_url(url)


settings = Settings()

