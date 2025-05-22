# app/api/routes/unidades.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas.unidades import UnidadCreate, UnidadUpdate, UnidadInDBBase
from app.services.unidades import UnidadService
from app.auth.firebase import require_role

router = APIRouter()

@router.get("/", response_model=List[UnidadInDBBase])
async def get_unidades(
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    return await UnidadService(db).get_by_company(user.company_id)

@router.get("/{unidad_id}", response_model=UnidadInDBBase)
async def get_unidad(
    unidad_id: UUID,
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    return await UnidadService(db).get_by_id_and_company(unidad_id, user.company_id)

@router.post("/", response_model=UnidadInDBBase, status_code=status.HTTP_201_CREATED)
async def create_unidad(
    unidad_in: UnidadCreate,
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    return await UnidadService(db).create(unidad_in, user.company_id)

@router.put("/{unidad_id}", response_model=UnidadInDBBase)
async def update_unidad(
    unidad_id: UUID,
    unidad_in: UnidadUpdate,
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    return await UnidadService(db).update(unidad_id, unidad_in, user.company_id)

@router.delete("/{unidad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unidad(
    unidad_id: UUID,
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    await UnidadService(db).delete(unidad_id, user.company_id)
