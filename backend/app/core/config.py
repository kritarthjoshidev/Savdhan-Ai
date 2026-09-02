import os
from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Surveillance Backend"
    PROJECT_VERSION: str = "0.1.0"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@postgres:5432/surveillance_db"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # MinIO
    MINIO_URL: str = os.getenv("MINIO_URL", "http://minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "surveillance")
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")
    LOCAL_STORAGE_DIR: str = os.getenv("LOCAL_STORAGE_DIR", "data")
    
    # MLflow
    MLFLOW_TRACKING_URI: str = os.getenv(
        "MLFLOW_TRACKING_URI",
        "http://mlflow:5000"
    )
    
    # Celery
    CELERY_BROKER_URL: str = os.getenv(
        "CELERY_BROKER_URL",
        "redis://redis:6379/0"
    )
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND",
        "redis://redis:6379/0"
    )
    
    # API
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # A few Windows launch environments set DEBUG=release/development.  Treat
    # these as false/true instead of failing during application import.
    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "development", "dev"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production", "prod", ""}:
                return False
        return value
    
    class Config:
        case_sensitive = True

settings = Settings()
