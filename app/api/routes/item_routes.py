from fastapi import APIRouter, Depends, Path, Query, status
from typing import List
from pydantic import UUID4

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.services import get_item_service
from app.services.item import ItemService
from app.db.models.user import User
from app.schemas.item import Item as ItemSchema, ItemCreate, ItemUpdate

router = APIRouter()

@router.get("/", response_model=List[ItemSchema])
async def read_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    item_service: ItemService = Depends(get_item_service)
):
    """
    Retrieve items
    """
    items = await item_service.get_active_items(skip=skip, limit=limit)
    return items

@router.post("/", response_model=ItemSchema, status_code=status.HTTP_201_CREATED)
async def create_item(
    item_in: ItemCreate,
    item_service: ItemService = Depends(get_item_service),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create new item
    """
    item = await item_service.create_item(item_in=item_in, owner_id=current_user.id)
    return item

@router.get("/me", response_model=List[ItemSchema])
async def read_user_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    item_service: ItemService = Depends(get_item_service),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's items
    """
    items = await item_service.get_user_items(
        owner_id=current_user.id, skip=skip, limit=limit
    )
    return items

@router.get("/{item_id}", response_model=ItemSchema)
async def read_item(
    item_id: UUID4 = Path(...),
    item_service: ItemService = Depends(get_item_service)
):
    """
    Get item by ID
    """
    item = await item_service.get_item(item_id=item_id)
    return item

@router.put("/{item_id}", response_model=ItemSchema)
async def update_item(
    item_in: ItemUpdate,
    item_id: UUID4 = Path(...),
    item_service: ItemService = Depends(get_item_service),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an item
    """
    item = await item_service.update_item(
        item_id=item_id, item_in=item_in, current_user_id=current_user.id
    )
    return item

@router.delete("/{item_id}", response_model=ItemSchema)
async def delete_item(
    item_id: UUID4 = Path(...),
    item_service: ItemService = Depends(get_item_service),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete an item
    """
    item = await item_service.delete_item(
        item_id=item_id, current_user_id=current_user.id
    )
    return item 