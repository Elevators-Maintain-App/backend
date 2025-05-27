from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.tipos_orden import TipoOrdenCreate, TipoOrdenUpdate, TipoOrdenInDBBase
from app.db.repositories.tipos_orden import tipo_orden_crud

router = APIRouter()

@router.get("/", response_model=List[TipoOrdenInDBBase])
async def get_tipos_orden(db: AsyncSession = Depends(get_db)):
    return await tipo_orden_crud.get_multi(db)

@router.get("/{tipo_orden_id}", response_model=TipoOrdenInDBBase)
async def get_tipo_orden(tipo_orden_id: int, db: AsyncSession = Depends(get_db)):
    tipo = await tipo_orden_crud.get(db, tipo_orden_id)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de orden no encontrado")
    return tipo

@router.post("/", response_model=TipoOrdenInDBBase, status_code=status.HTTP_201_CREATED)
async def create_tipo_orden(tipo_in: TipoOrdenCreate, db: AsyncSession = Depends(get_db)):
    existing = await tipo_orden_crud.get_by_field(db, field="nombre", value=tipo_in.nombre)
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un tipo de orden con ese nombre.")
    return await tipo_orden_crud.create(db, obj_in=tipo_in)
