# app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://localhost:5432/alhanger"
    # AUTH0_DOMAIN: str = None
    # AUTH0_API_AUDIENCE: str = None
    AUTH0_ALGORITHMS: list = ["RS256"]
    CACHE_DIR: str = "./cache"
    MAX_CACHE_SIZE_GB: int = 10
    
    class Config:
        env_file = ".env"
        extra = "allow"

@lru_cache()
def get_settings():
    return Settings()