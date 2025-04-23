from typing import List
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ForbiddenException
from app.db.repositories.item import ItemRepository
from app.db.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate

class ItemService:
    def __init__(self, db: AsyncSession):
        self.repository = ItemRepository(db)
    
    async def get_item(self, item_id: UUID4) -> Item:
        """
        Get an item by ID
        """
        item = await self.repository.get(item_id)
        if not item:
            raise NotFoundException(f"Item with ID {item_id} not found")
        return item
    
    async def get_items(self, skip: int = 0, limit: int = 100) -> List[Item]:
        """
        Get all items
        """
        return await self.repository.list(skip=skip, limit=limit)
    
    async def get_active_items(self, skip: int = 0, limit: int = 100) -> List[Item]:
        """
        Get all active items
        """
        return await self.repository.get_active_items(skip=skip, limit=limit)
    
    async def get_user_items(self, owner_id: UUID4, skip: int = 0, limit: int = 100) -> List[Item]:
        """
        Get all items owned by a user
        """
        return await self.repository.get_by_owner(owner_id=owner_id, skip=skip, limit=limit)
    
    async def create_item(self, item_in: ItemCreate, owner_id: UUID4) -> Item:
        """
        Create a new item
        """
        item_data = item_in.model_dump()
        item_data["owner_id"] = owner_id
        
        # Create the item
        item = await self.repository.create(obj_in=ItemCreate(**item_data))
        return item
    
    async def update_item(self, item_id: UUID4, item_in: ItemUpdate, current_user_id: UUID4) -> Item:
        """
        Update an item
        """
        item = await self.get_item(item_id)
        
        # Check if user is the owner of the item
        if item.owner_id != current_user_id:
            raise ForbiddenException("You don't have permission to update this item")
        
        update_data = item_in.model_dump(exclude_unset=True)
        updated_item = await self.repository.update(db_obj=item, obj_in=update_data)
        return updated_item
    
    async def delete_item(self, item_id: UUID4, current_user_id: UUID4) -> Item:
        """
        Delete an item
        """
        item = await self.get_item(item_id)
        
        # Check if user is the owner of the item
        if item.owner_id != current_user_id:
            raise ForbiddenException("You don't have permission to delete this item")
        
        deleted_item = await self.repository.delete(id=item_id)
        return deleted_item 