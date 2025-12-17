"""
Application configuration using Pydantic Settings
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    ADMIN_PREFIX: str = "/api/v1/admin"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # Database
    DATABASE_URL: str = "postgresql://admin:dev_password@localhost:5432/naad_bailgada"

    # JWT Authentication
    JWT_SECRET_KEY: str = "your_secret_key_here_minimum_32_characters_long"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: str = "http://localhost:8000,http://localhost:9000,http://localhost:8081,http://127.0.0.1:8000,http://127.0.0.1:9000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/jpg"
    UPLOAD_DIR: str = "./uploads"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def allowed_image_types_list(self) -> List[str]:
        return [t.strip() for t in self.ALLOWED_IMAGE_TYPES.split(",")]

    # GCP
    GCP_PROJECT_ID: str = ""
    GCP_BUCKET_NAME: str = "" 
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    CLOUD_SQL_CONNECTION_NAME: str = ""
    USE_CLOUD_SQL: bool = False

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100


    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Create settings instance
settings = Settings()
