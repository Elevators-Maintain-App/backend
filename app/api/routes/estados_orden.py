from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.estados_orden import EstadoOrdenCreate, EstadoOrdenUpdate, EstadoOrdenInDBBase
from app.db.repositories.estados_orden import estado_orden_crud
from app.auth.firebase import require_role

router = APIRouter()

@router.get("/", response_model=List[EstadoOrdenInDBBase])
async def get_estados_orden(db: AsyncSession = Depends(get_db)):
    return await estado_orden_crud.get_multi(db)

@router.get("/{estado_orden_id}", response_model=EstadoOrdenInDBBase)
async def get_estado_orden(estado_orden_id: int, db: AsyncSession = Depends(get_db)):
    estado = await estado_orden_crud.get(db, estado_orden_id)
    if not estado:
        raise HTTPException(status_code=404, detail="Estado de orden no encontrado")
    return estado

@router.post("/", response_model=EstadoOrdenInDBBase, status_code=status.HTTP_201_CREATED)
async def create_estado_orden(
    estado_in: EstadoOrdenCreate,
    _user=Depends(require_role("superAdmin", "admin")),
    db: AsyncSession = Depends(get_db),
):
    existing = await estado_orden_crud.get_by_field(db, field="nombre", value=estado_in.nombre)
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un estado de orden con ese nombre.")
    return await estado_orden_crud.create(db, obj_in=estado_in)
