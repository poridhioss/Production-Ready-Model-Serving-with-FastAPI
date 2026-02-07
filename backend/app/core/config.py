from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Sentiment Analysis API"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    
    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://localhost:8000"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()