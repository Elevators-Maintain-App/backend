from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import UUID4

from app.db.repositories.base import BaseRepository
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=User, db=db)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email
        """
        return await self.get_by_field("email", email)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username
        """
        return await self.get_by_field("username", username)
    
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all active users
        """
        query = select(self.model).where(self.model.is_active == True).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all() 