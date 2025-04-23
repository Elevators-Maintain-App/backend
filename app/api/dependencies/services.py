from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.user import UserService
from app.services.item import ItemService
from app.services.auth import AuthService

async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """
    Dependency to get a UserService instance
    """
    return UserService(db)

async def get_item_service(db: AsyncSession = Depends(get_db)) -> ItemService:
    """
    Dependency to get an ItemService instance
    """
    return ItemService(db)

async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """
    Dependency to get an AuthService instance
    """
    return AuthService(db)