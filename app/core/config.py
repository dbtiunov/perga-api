import logging

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Perga API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    IS_DEV: bool = True
    SECRET_KEY: str = 'your-secret-key'
    LOGGING_LEVEL: int = logging.INFO
    CORS_ORIGINS: list[str] = ['*']

    POSTGRES_HOST: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None

    ROOT_URL_REDIRECT: Optional[str] = None

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f'postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}/{self.POSTGRES_DB}'

    class Config:
        env_file = ".env"
        case_sensitive = True
        cache_enabled = False

settings = Settings()
