from enum import Enum
from typing import Any, Dict, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl


class AppEnvTypes(Enum):
    PROD: str = "prod"
    DEV: str = "dev"
    TEST: str = "test"


class BaseAppSettings(BaseSettings):
    app_env: AppEnvTypes = AppEnvTypes.DEV

    class Config:
        env_file = ".env"
        extra = "ignore"


class Settings(BaseAppSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "CHRONOHUB"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str
    POOL_SIZE: int = 40
    MAX_OVERFLOW: int = 5
    POOL_RECYCLE: int = 600
    # API
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="allow"
    )
    TEST: str

    @property
    def fastapi_kwargs(self) -> Dict[str, Any]:
        return {
            "title": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "openapi_url": f"{settings.API_V1_PREFIX}/openapi.json",
            "docs_url": f"{settings.API_V1_PREFIX}/docs",
            "redoc_url": f"{settings.API_V1_PREFIX}/redoc",
        }


settings = Settings()
