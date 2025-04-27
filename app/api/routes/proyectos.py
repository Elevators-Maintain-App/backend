# app/api/routes/proyectos.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas.proyectos import ProyectoCreate, ProyectoUpdate, ProyectoInDBBase
from app.services.proyectos import ProyectoService

router = APIRouter(prefix="/proyectos", tags=["Proyectos"])

@router.get("/", response_model=List[ProyectoInDBBase])
async def get_proyectos(db: AsyncSession = Depends(get_db)):
    service = ProyectoService(db)
    return await service.get_all()

@router.get("/{proyecto_id}", response_model=ProyectoInDBBase)
async def get_proyecto(proyecto_id: UUID, db: AsyncSession = Depends(get_db)):
    service = ProyectoService(db)
    return await service.get_by_id(proyecto_id)

@router.post("/", response_model=ProyectoInDBBase, status_code=status.HTTP_201_CREATED)
async def create_proyecto(proyecto_in: ProyectoCreate, db: AsyncSession = Depends(get_db)):
    service = ProyectoService(db)
    return await service.create(proyecto_in)

@router.put("/{proyecto_id}", response_model=ProyectoInDBBase)
async def update_proyecto(proyecto_id: UUID, proyecto_in: ProyectoUpdate, db: AsyncSession = Depends(get_db)):
    service = ProyectoService(db)
    return await service.update(proyecto_id, proyecto_in)

@router.delete("/{proyecto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proyecto(proyecto_id: UUID, db: AsyncSession = Depends(get_db)):
    service = ProyectoService(db)
    await service.delete(proyecto_id)
