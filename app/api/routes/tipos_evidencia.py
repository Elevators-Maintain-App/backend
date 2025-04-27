from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.tipos_evidencia import TipoEvidenciaCreate, TipoEvidenciaUpdate, TipoEvidenciaInDBBase
from app.db.repositories.tipos_evidencia import tipo_evidencia_crud

router = APIRouter()

@router.get("/", response_model=List[TipoEvidenciaInDBBase])
async def get_tipos_evidencia(db: AsyncSession = Depends(get_db)):
    return await tipo_evidencia_crud.get_multi(db)

@router.get("/{tipo_evidencia_id}", response_model=TipoEvidenciaInDBBase)
async def get_tipo_evidencia(tipo_evidencia_id: int, db: AsyncSession = Depends(get_db)):
    tipo = await tipo_evidencia_crud.get(db, tipo_evidencia_id)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de evidencia no encontrado")
    return tipo

@router.post("/", response_model=TipoEvidenciaInDBBase, status_code=status.HTTP_201_CREATED)
async def create_tipo_evidencia(tipo_in: TipoEvidenciaCreate, db: AsyncSession = Depends(get_db)):
    existing = await tipo_evidencia_crud.get_by_field(db, field="nombre", value=tipo_in.nombre)
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un tipo de evidencia con ese nombre.")
    return await tipo_evidencia_crud.create(db, obj_in=tipo_in)
