"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "YouTube Mind Map Tool"
    
    # CORS Configuration
    ALLOWED_HOSTS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    # Database Configuration
    DATABASE_URL: Optional[str] = None
    SQLITE_DB_PATH: str = "app.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # External APIs
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    YOUTUBE_API_KEY: Optional[str] = None
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # Application Settings
    MOCK_MODE: bool = True
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def database_url(self) -> str:
        """Get database URL"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"sqlite:///{self.SQLITE_DB_PATH}"


# Create global settings instance
settings = Settings()