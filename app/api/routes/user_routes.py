from fastapi import APIRouter, Depends, Path, Query, status
from typing import List
from pydantic import UUID4

from app.api.dependencies.auth import get_current_active_user, get_current_superuser
from app.api.dependencies.services import get_user_service
from app.services.user import UserService
from app.db.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate

router = APIRouter()

@router.get("/", response_model=List[UserSchema])
async def read_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_superuser)
):
    """
    Retrieve users - superuser only
    """
    users = await user_service.get_users(skip=skip, limit=limit)
    return users

@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Create new user
    """
    user = await user_service.create_user(user_in=user_in)
    return user

@router.get("/me", response_model=UserSchema)
async def read_user_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user
    """
    return current_user

@router.put("/me", response_model=UserSchema)
async def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update current user
    """
    updated_user = await user_service.update_user(
        user_id=current_user.id, user_in=user_in
    )
    return updated_user

@router.get("/{user_id}", response_model=UserSchema)
async def read_user_by_id(
    user_id: UUID4 = Path(...),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific user by id
    """
    user = await user_service.get_user(user_id=user_id)
    return user

@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_in: UserUpdate,
    user_id: UUID4 = Path(...),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_superuser)
):
    """
    Update a user - superuser only
    """
    user = await user_service.update_user(
        user_id=user_id, user_in=user_in
    )
    return user

@router.delete("/{user_id}", response_model=UserSchema)
async def delete_user(
    user_id: UUID4 = Path(...),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_superuser)
):
    """
    Delete a user - superuser only
    """
    user = await user_service.delete_user(user_id=user_id)
    return user 