# app/api/routes/checklists.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas.checklists import ChecklistCreate, ChecklistUpdate, ChecklistInDBBase
from app.services.checklists import ChecklistService

router = APIRouter(prefix="/checklists", tags=["Checklists"])

@router.get("/", response_model=List[ChecklistInDBBase])
async def get_checklists(db: AsyncSession = Depends(get_db)):
    service = ChecklistService(db)
    return await service.get_all()

@router.get("/{checklist_id}", response_model=ChecklistInDBBase)
async def get_checklist(checklist_id: UUID, db: AsyncSession = Depends(get_db)):
    service = ChecklistService(db)
    return await service.get_by_id(checklist_id)

@router.post("/", response_model=ChecklistInDBBase, status_code=status.HTTP_201_CREATED)
async def create_checklist(checklist_in: ChecklistCreate, db: AsyncSession = Depends(get_db)):
    service = ChecklistService(db)
    return await service.create(checklist_in)

@router.put("/{checklist_id}", response_model=ChecklistInDBBase)
async def update_checklist(checklist_id: UUID, checklist_in: ChecklistUpdate, db: AsyncSession = Depends(get_db)):
    service = ChecklistService(db)
    return await service.update(checklist_id, checklist_in)

@router.delete("/{checklist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checklist(checklist_id: UUID, db: AsyncSession = Depends(get_db)):
    service = ChecklistService(db)
    await service.delete(checklist_id)
