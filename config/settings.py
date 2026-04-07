from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    """App configuration loaded from the .env file."""
    JWT_SECRET_KEY: str
    GEMINI_API_KEY: str
    
    DATABASE_URL: str
    REDIS_URL: str
    
    PHISHING_THRESHOLD: float = 0.80
    MALICIOUS_CODE_THRESHOLD: float = 0.85

    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()