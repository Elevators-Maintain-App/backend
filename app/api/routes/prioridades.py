from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.prioridades import PrioridadCreate, PrioridadUpdate, PrioridadInDBBase
from app.db.repositories.prioridades import prioridad_crud

router = APIRouter()

@router.get("/", response_model=List[PrioridadInDBBase])
async def get_prioridades(db: AsyncSession = Depends(get_db)):
    return await prioridad_crud.get_multi(db)

@router.get("/{prioridad_id}", response_model=PrioridadInDBBase)
async def get_prioridad(prioridad_id: int, db: AsyncSession = Depends(get_db)):
    prioridad = await prioridad_crud.get(db, prioridad_id)
    if not prioridad:
        raise HTTPException(status_code=404, detail="Prioridad no encontrada")
    return prioridad

@router.post("/", response_model=PrioridadInDBBase, status_code=status.HTTP_201_CREATED)
async def create_prioridad(prioridad_in: PrioridadCreate, db: AsyncSession = Depends(get_db)):
    existing = await prioridad_crud.get_by_field(db, field="nombre", value=prioridad_in.nombre)
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe una prioridad con ese nombre.")
    return await prioridad_crud.create(db, obj_in=prioridad_in)
