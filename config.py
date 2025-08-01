import os
from typing import List
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/aqlify_db")
    
    # Redis Cache
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]  # Configure for production
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    
    # Forecasting
    DEFAULT_FORECAST_DAYS: int = 30
    MIN_HISTORICAL_DAYS: int = 14
    MAX_FORECAST_DAYS: int = 365
    
    # Business Tiers
    FREE_TIER_FORECASTS_PER_MONTH: int = 100
    PREMIUM_TIER_FORECASTS_PER_MONTH: int = 1000
    ENTERPRISE_TIER_FORECASTS_PER_MONTH: int = 10000
    
    class Config:
        env_file = ".env"

settings = Settings()
