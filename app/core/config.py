import os
from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, Union

class Settings(BaseSettings):
    # Application settings
    app_name: str = "FastAPI Layered App"
    debug: bool = False
    environment: Optional[str] = None
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", 8000))
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", 5432))
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "postgres")
    db_name: str = os.getenv("DB_NAME", "postgres")
    
    # Database settings - will be constructed based on environment
    database_url: Optional[str] = os.getenv("DATABASE_URL")
    
    @field_validator('database_url', mode='before')
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> str:        
        data = info.data
        environment = data.get("environment")
        data_base_url = data.get("database_url")
        
        logging.debug(f"🔍 Environment: {environment}")
        
        if environment == 'development':
            db_user = data.get('db_user')   
            db_password = data.get('db_password')
            db_host = data.get('db_host')
            db_port = data.get('db_port')
            db_name = data.get('db_name')
            constructed_url = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            print(f"🏠 Development DB")  
            return constructed_url
        
        database_url_from_env = os.getenv("DATABASE_URL")

        if database_url_from_env:
            if database_url_from_env.startswith("postgresql://"):
                database_url_from_env = database_url_from_env.replace("postgresql://", "postgresql+asyncpg://", 1)
            print(f"☁️ Production DB")
            return database_url_from_env
            
        fallback_url = f"postgresql+asyncpg://{data.get('db_user')}:{data.get('db_password')}@{data.get('db_host')}:{data.get('db_port')}/{data.get('db_name')}"
        print(f"🔄 Fallback DB: {fallback_url}")
        return fallback_url
    
    # JWT settings
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Define additional settings here    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow"  # Allow extra environment variables
    }

# Create settings instance
settings = Settings()

