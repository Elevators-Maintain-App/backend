from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.tipos_unidad import TipoUnidadCreate, TipoUnidadUpdate, TipoUnidadInDBBase
from app.db.repositories.tipos_unidad import tipo_unidad_crud
from app.auth.firebase import require_role

router = APIRouter()

@router.get("/", response_model=List[TipoUnidadInDBBase])
async def get_tipos_unidad(db: AsyncSession = Depends(get_db)):
    return await tipo_unidad_crud.get_multi(db)

@router.get("/{tipo_unidad_id}", response_model=TipoUnidadInDBBase)
async def get_tipo_unidad(tipo_unidad_id: int, db: AsyncSession = Depends(get_db)):
    tipo = await tipo_unidad_crud.get(db, tipo_unidad_id)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de unidad no encontrado")
    return tipo

@router.post("/", response_model=TipoUnidadInDBBase, status_code=status.HTTP_201_CREATED)
async def create_tipo_unidad(
    tipo_in: TipoUnidadCreate,
    _user=Depends(require_role("superAdmin", "admin")),
    db: AsyncSession = Depends(get_db),
):
    existing = await tipo_unidad_crud.get_by_field(db, field="nombre", value=tipo_in.nombre)
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un tipo de unidad con ese nombre.")
    return await tipo_unidad_crud.create(db, obj_in=tipo_in)
