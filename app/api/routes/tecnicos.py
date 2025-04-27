# app/api/routes/tecnicos.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas.tecnicos import TecnicoCreate, TecnicoUpdate, TecnicoInDBBase
from app.schemas.ordenes_de_trabajo import OrdenDeTrabajoInDBBase
from app.schemas.checklists import ChecklistInDBBase
from app.services.tecnicos import TecnicoService

router = APIRouter(prefix="/tecnicos", tags=["Técnicos"])

# Rutas CRUD normales
@router.get("/", response_model=List[TecnicoInDBBase])
async def get_tecnicos(db: AsyncSession = Depends(get_db)):
    service = TecnicoService(db)
    return await service.get_all()

@router.get("/{tecnico_id}", response_model=TecnicoInDBBase)
async def get_tecnico(tecnico_id: UUID, db: AsyncSession = Depends(get_db)):
    service = TecnicoService(db)
    return await service.get_by_id(tecnico_id)

@router.post("/", response_model=TecnicoInDBBase, status_code=status.HTTP_201_CREATED)
async def create_tecnico(tecnico_in: TecnicoCreate, db: AsyncSession = Depends(get_db)):
    service = TecnicoService(db)
    return await service.create(tecnico_in)

@router.put("/{tecnico_id}", response_model=TecnicoInDBBase)
async def update_tecnico(tecnico_id: UUID, tecnico_in: TecnicoUpdate, db: AsyncSession = Depends(get_db)):
    service = TecnicoService(db)
    return await service.update(tecnico_id, tecnico_in)

@router.delete("/{tecnico_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tecnico(tecnico_id: UUID, db: AsyncSession = Depends(get_db)):
    service = TecnicoService(db)
    await service.delete(tecnico_id)

# Rutas Especiales 🔥

@router.get("/{tecnico_id}/ordenes-trabajo", response_model=List[OrdenDeTrabajoInDBBase], description="Listar todas las órdenes de trabajo asignadas a un técnico.")
async def get_ordenes_tecnico(tecnico_id: UUID, db: AsyncSession = Depends(get_db)):
    service = TecnicoService(db)
    return await service.get_ordenes_trabajo(tecnico_id)

@router.get("/{tecnico_id}/checklists", response_model=List[ChecklistInDBBase], description="Listar todos los checklists realizados por un técnico.")
async def get_checklists_tecnico(tecnico_id: UUID, db: AsyncSession = Depends(get_db)):
    service = TecnicoService(db)
    return await service.get_checklists(tecnico_id)
