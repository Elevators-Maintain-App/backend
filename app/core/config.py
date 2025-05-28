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
    port: int = 8000
    
    # Database settings
    db_user: str
    db_password: str
    db_host: str
    db_port: str
    db_name: str
    database_url: Optional[PostgresDsn] = None
    
    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_url(cls, v: Optional[str], info) -> Any:
        if v and isinstance(v, str):
            return v
        
        # En Pydantic v2, debemos usar info.data para acceder a los demás campos
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=info.data.get("db_user"),
            password=info.data.get("db_password"),
            host=info.data.get("db_host"),
            port=int(info.data.get("db_port")),
            path=f"{info.data.get('db_name') or ''}",
        )
    
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

# Print settings in development mode
if settings.environment == "development":
    print(f"Running in {settings.environment} mode")
    # Avoid printing sensitive information in logs
    safe_settings = settings.model_dump(exclude={"secret_key", "db_password"})
    for key, value in safe_settings.items():
        print(f"{key}: {value}") 