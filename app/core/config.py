# app/core/config.py
from typing import List

from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/luce-di-villa"

    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # File uploads
    UPLOAD_DIR: str = "uploads"

    MEDIA_UPLOAD_DIR: str = "uploads/media"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_IMAGE_TYPES: set = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
    ALLOWED_VIDEO_TYPES: set = {"video/mp4", "video/avi", "video/mov", "video/wmv", "video/webm"}

    class Config:
        env_file = ".env"


settings = Settings()
