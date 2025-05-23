# app/api/routes/zonas_geograficas.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas.zonas_geograficas import ZonaGeograficaCreate, ZonaGeograficaUpdate, ZonaGeograficaInDBBase
from app.services.zonas_geograficas import ZonaGeograficaService

router = APIRouter()

# CRUD zonas geograficas

@router.get("/", response_model=List[ZonaGeograficaInDBBase])
async def get_zonas_geograficas(db: AsyncSession = Depends(get_db)):
    service = ZonaGeograficaService(db)
    return await service.get_all()

@router.get("/{zona_id}", response_model=ZonaGeograficaInDBBase)
async def get_zona_geografica(zona_id: UUID, db: AsyncSession = Depends(get_db)):
    service = ZonaGeograficaService(db)
    return await service.get_by_id(zona_id)

@router.post("/", response_model=ZonaGeograficaInDBBase, status_code=status.HTTP_201_CREATED)
async def create_zona_geografica(zona_in: ZonaGeograficaCreate, db: AsyncSession = Depends(get_db)):
    service = ZonaGeograficaService(db)
    return await service.create(zona_in)

@router.put("/{zona_id}", response_model=ZonaGeograficaInDBBase)
async def update_zona_geografica(zona_id: UUID, zona_in: ZonaGeograficaUpdate, db: AsyncSession = Depends(get_db)):
    service = ZonaGeograficaService(db)
    return await service.update(zona_id, zona_in)

@router.delete("/{zona_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zona_geografica(zona_id: UUID, db: AsyncSession = Depends(get_db)):
    service = ZonaGeograficaService(db)
    await service.delete(zona_id)
