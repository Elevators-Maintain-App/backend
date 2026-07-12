# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.database_safety import validate_safe_test_database
from app.core.config import settings

if settings.environment == "test":
    validate_safe_test_database(settings.environment, str(settings.database_url))

# Create async engine
engine = create_async_engine(
    str(settings.database_url),
    echo=False,
    future=True,
    pool_pre_ping=True,
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

AsyncSessionLocal = async_session

# Create declarative base for models
Base = declarative_base()

# Dependency for database session
async def get_db():
    """
    Dependency that provides an async database session
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
