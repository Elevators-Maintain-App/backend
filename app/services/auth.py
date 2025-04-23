from datetime import datetime, timedelta
from typing import Optional, Union
from jose import jwt
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.services.user import UserService
from app.db.models.user import User
from app.schemas.token import TokenPayload

class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_service = UserService(db)
    
    def create_access_token(
        self, subject: Union[str, UUID4], expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.access_token_expire_minutes
            )
        
        to_encode = {"exp": expire, "sub": str(subject)}
        encoded_jwt = jwt.encode(
            to_encode, settings.secret_key, algorithm=settings.algorithm
        )
        return encoded_jwt
    
    def decode_token(self, token: str) -> TokenPayload:
        """
        Decode a JWT token
        """
        try:
            payload = jwt.decode(
                token, settings.secret_key, algorithms=[settings.algorithm]
            )
            token_data = TokenPayload(**payload)
            
            if datetime.fromtimestamp(token_data.exp) < datetime.utcnow():
                raise UnauthorizedException("Token expired")
                
            return token_data
        except jwt.JWTError:
            raise UnauthorizedException("Invalid token")
    
    async def authenticate_user(self, username: str, password: str) -> User:
        """
        Authenticate a user
        """
        user = await self.user_service.authenticate_user(username, password)
        if not user:
            raise UnauthorizedException("Incorrect username or password")
        if not user.is_active:
            raise UnauthorizedException("Inactive user")
        return user
    
    async def get_current_user(self, token: str) -> User:
        """
        Get the current user from a token
        """
        token_data = self.decode_token(token)
        user = await self.user_service.get_user_by_username(token_data.sub)
        
        if not user:
            raise UnauthorizedException("User not found")
        if not user.is_active:
            raise UnauthorizedException("Inactive user")
            
        return user 