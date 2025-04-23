from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import UUID4

from app.db.repositories.base import BaseRepository
from app.db.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate

class ItemRepository(BaseRepository[Item, ItemCreate, ItemUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Item, db=db)
    
    async def get_by_owner(self, owner_id: UUID4, skip: int = 0, limit: int = 100) -> List[Item]:
        """
        Get all items by owner
        """
        query = (
            select(self.model)
            .where(self.model.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_active_items(self, skip: int = 0, limit: int = 100) -> List[Item]:
        """
        Get all active items
        """
        query = (
            select(self.model)
            .where(self.model.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all() 