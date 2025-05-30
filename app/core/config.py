import os
from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, Union

class Settings(BaseSettings):
    # Application settings
    app_name: str = "FastAPI Layered App"
    debug: bool = False
    environment: str = "development"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", 8000))
    
    # Database settings
    database_url: PostgresDsn
    
    # JWT settings
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Define additional settings here
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }

# Create settings instance
settings = Settings()

