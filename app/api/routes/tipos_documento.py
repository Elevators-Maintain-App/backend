# app/api/routes/tipos_documento.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.tipos_documento import TipoDocumentoCreate, TipoDocumentoUpdate, TipoDocumentoInDBBase
from app.db.repositories.tipos_documento import tipo_documento_crud
from app.auth.firebase import require_role

router = APIRouter()

@router.get("/", response_model=List[TipoDocumentoInDBBase])
async def get_tipos_documento(db: AsyncSession = Depends(get_db)):
    return await tipo_documento_crud.get_multi(db)

@router.get("/{tipo_documento_id}", response_model=TipoDocumentoInDBBase)
async def get_tipo_documento(tipo_documento_id: int, db: AsyncSession = Depends(get_db)):
    tipo_documento_obj = await tipo_documento_crud.get(db, tipo_documento_id)
    if not tipo_documento_obj:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado")
    return tipo_documento_obj

@router.post("/", response_model=TipoDocumentoInDBBase, status_code=status.HTTP_201_CREATED)
async def create_tipo_documento(
    tipo_documento_in: TipoDocumentoCreate,
    _user=Depends(require_role("superAdmin", "admin")),
    db: AsyncSession = Depends(get_db),
):
    existing = await tipo_documento_crud.get_by_field(db, field="nombre", value=tipo_documento_in.nombre)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un tipo de documento con ese nombre."
        )
    return await tipo_documento_crud.create(db, obj_in=tipo_documento_in)
