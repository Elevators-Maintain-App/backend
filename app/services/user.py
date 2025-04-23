from typing import List, Optional
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.core.exceptions import NotFoundException, ConflictException
from app.db.repositories.user import UserRepository
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import get_password_hash, verify_password

class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)
    
    async def get_user(self, user_id: UUID4) -> User:
        """
        Get a user by ID
        """
        user = await self.repository.get(user_id)
        if not user:
            raise NotFoundException(f"User with ID {user_id} not found")
        return user
    
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all users
        """
        return await self.repository.list(skip=skip, limit=limit)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email
        """
        return await self.repository.get_by_email(email)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username
        """
        return await self.repository.get_by_username(username)
    
    async def create_user(self, user_in: UserCreate) -> User:
        """
        Create a new user
        """
        # Check if email exists
        existing_user = await self.repository.get_by_email(user_in.email)
        if existing_user:
            raise ConflictException(f"Email {user_in.email} already registered")
        
        # Check if username exists
        existing_user = await self.repository.get_by_username(user_in.username)
        if existing_user:
            raise ConflictException(f"Username {user_in.username} already taken")
        
        # Hash password
        hashed_password = get_password_hash(user_in.password)
        user_data = user_in.model_dump()
        user_data.pop("password")
        user_data["hashed_password"] = hashed_password
        
        # Create user with modified data
        user = await self.repository.create(obj_in=UserCreate(**user_data))
        return user
    
    async def update_user(self, user_id: UUID4, user_in: UserUpdate) -> User:
        """
        Update a user
        """
        user = await self.get_user(user_id)
        
        # Check if email exists and is different from current user
        if user_in.email and user_in.email != user.email:
            existing_user = await self.repository.get_by_email(user_in.email)
            if existing_user:
                raise ConflictException(f"Email {user_in.email} already registered")
        
        # Check if username exists and is different from current user
        if user_in.username and user_in.username != user.username:
            existing_user = await self.repository.get_by_username(user_in.username)
            if existing_user:
                raise ConflictException(f"Username {user_in.username} already taken")
        
        # Handle password update
        update_data = user_in.model_dump(exclude_unset=True)
        if user_in.password:
            hashed_password = get_password_hash(user_in.password)
            update_data.pop("password", None)
            update_data["hashed_password"] = hashed_password
        
        updated_user = await self.repository.update(db_obj=user, obj_in=update_data)
        return updated_user
    
    async def delete_user(self, user_id: UUID4) -> User:
        """
        Delete a user
        """
        user = await self.get_user(user_id)
        deleted_user = await self.repository.delete(id=user_id)
        return deleted_user
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user by username and password
        """
        user = await self.repository.get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user 