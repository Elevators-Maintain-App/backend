from pydantic import BaseModel, EmailStr, Field, UUID4
from typing import Optional
from datetime import datetime

# Base User Schema
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False

# Schema for creating a user
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

# Schema for updating a user
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

# Schema for user in response
class User(UserBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

# Schema for user in login response
class UserInDB(User):
    hashed_password: str

    model_config = {
        "from_attributes": True
    } 