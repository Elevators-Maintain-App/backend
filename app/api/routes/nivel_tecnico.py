from fastapi import APIRouter
from typing import List
from app.schemas.nivel_tecnico import NivelTecnico, NivelTecnicoCreate, NivelTecnicoUpdate
from uuid import UUID
from app.services.usuario.nivel_tecnico import NivelTecnicoService
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.auth.firebase import require_role

router = APIRouter()

@router.get("/", response_model=List[NivelTecnico])
async def get_nivel_tecnico(
    db: AsyncSession = Depends(get_db),
):
    nivel_tecnico_service = NivelTecnicoService(db)
    return await nivel_tecnico_service.get_niveles_tecnicos()

@router.post("/")
async def create_nivel_tecnico(
    nivel_tecnico: NivelTecnicoCreate,
    user=Depends(require_role("admin", "superAdmin", "supervisor")),
    db: AsyncSession = Depends(get_db),
):
    nivel_tecnico_service = NivelTecnicoService(db)
    return await nivel_tecnico_service.create_nivel_tecnico(nivel_tecnico)

@router.put("/{nivel_tecnico_id}")
async def update_nivel_tecnico(nivel_tecnico_id: UUID, nivel_tecnico: NivelTecnicoUpdate,
    user=Depends(require_role("admin", "superAdmin", "supervisor")),
    db: AsyncSession = Depends(get_db),
):
    nivel_tecnico_service = NivelTecnicoService(db)
    return await nivel_tecnico_service.update_nivel_tecnico(nivel_tecnico_id, nivel_tecnico)

@router.delete("/{nivel_tecnico_id}")
async def delete_nivel_tecnico(
    nivel_tecnico_id: UUID,
    user=Depends(require_role("admin", "superAdmin", "supervisor")),
    db: AsyncSession = Depends(get_db),
):
    nivel_tecnico_service = NivelTecnicoService(db)
    return await nivel_tecnico_service.delete_nivel_tecnico(nivel_tecnico_id)