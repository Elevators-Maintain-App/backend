import os
from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, Union

class Settings(BaseSettings):
    # Application settings
    app_name: str = "VertiOne API"
    debug: bool = False
    environment: Optional[str] = None
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Database settings
    database_url: str

    # Notification settings
    notification_email: str
    email_pwd: str
    smtp_server: str
    smtp_port: str
    email_timeout: int
    
    # JWT settings
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

# Create settings instance
settings = Settings()

