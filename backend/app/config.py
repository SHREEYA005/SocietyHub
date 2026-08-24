"""
Centralized application configuration.
All values are loaded from environment variables (see .env.example).
Nothing sensitive is hardcoded here.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Core ---
    APP_NAME: str = "SocietyHub"
    ENVIRONMENT: str = "development"

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./societyhub.db"

    # --- Auth ---
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # --- Overdue detection ---
    OVERDUE_THRESHOLD_DAYS: int = 3

    # --- File storage ---
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 5
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/webp"

    # --- Email (SMTP). If EMAIL_HOST is empty, emails are logged, not sent. ---
    EMAIL_HOST: str = ""
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_FROM: str = "no-reply@societyhub.local"
    EMAIL_USE_TLS: bool = True

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def allowed_image_types_list(self):
        return [t.strip() for t in self.ALLOWED_IMAGE_TYPES.split(",") if t.strip()]

    @property
    def cors_origins_list(self):
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
