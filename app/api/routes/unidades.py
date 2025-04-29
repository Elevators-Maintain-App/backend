# app/api/routes/unidades.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas.unidades import UnidadCreate, UnidadUpdate, UnidadInDBBase
from app.services.unidades import UnidadService

router = APIRouter()

@router.get("/", response_model=List[UnidadInDBBase])
async def get_unidades(db: AsyncSession = Depends(get_db)):
    service = UnidadService(db)
    return await service.get_all()

@router.get("/{unidad_id}", response_model=UnidadInDBBase)
async def get_unidad(unidad_id: UUID, db: AsyncSession = Depends(get_db)):
    service = UnidadService(db)
    return await service.get_by_id(unidad_id)

@router.post("/", response_model=UnidadInDBBase, status_code=status.HTTP_201_CREATED)
async def create_unidad(unidad_in: UnidadCreate, db: AsyncSession = Depends(get_db)):
    service = UnidadService(db)
    return await service.create(unidad_in)

@router.put("/{unidad_id}", response_model=UnidadInDBBase)
async def update_unidad(unidad_id: UUID, unidad_in: UnidadUpdate, db: AsyncSession = Depends(get_db)):
    service = UnidadService(db)
    return await service.update(unidad_id, unidad_in)

@router.delete("/{unidad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unidad(unidad_id: UUID, db: AsyncSession = Depends(get_db)):
    service = UnidadService(db)
    await service.delete(unidad_id)
