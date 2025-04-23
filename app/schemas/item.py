from pydantic import BaseModel, Field, UUID4
from typing import Optional
from datetime import datetime

# Base Item Schema
class ItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    is_active: bool = True

# Schema for creating an item
class ItemCreate(ItemBase):
    pass

# Schema for updating an item
class ItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None

# Schema for item in response
class Item(ItemBase):
    id: UUID4
    owner_id: UUID4
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

# Schema for item with owner details
class ItemWithOwner(Item):
    owner: "UserBase"

    model_config = {
        "from_attributes": True
    }

# Forward reference resolution
from app.schemas.user import UserBase  # noqa: E402
ItemWithOwner.model_rebuild() 