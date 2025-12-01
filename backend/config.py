import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # Security
    encryption_key: str = Field(..., env="ENCRYPTION_KEY")
    jwt_secret: str = Field(..., env="JWT_SECRET")
    
    # Database
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_key: str = Field(..., env="SUPABASE_KEY")
    
    # CORS
    frontend_url: str = Field("http://localhost:3000", env="FRONTEND_URL")
    
    # API
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    
    class Config:
        env_file = ".env"


settings = Settings()