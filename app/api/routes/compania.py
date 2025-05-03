from fastapi import APIRouter, Depends, Path, Query, status, HTTPException
from typing import List, Optional
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

from app.services.compania import CompaniaService
from app.db.models.usuarios import Usuario
from app.schemas.compania import Compania as CompaniaSchema
from app.schemas.compania import CompaniaCreate, CompaniaUpdate, CompaniaWithRelations

router = APIRouter()

@router.get("/", response_model=List[CompaniaSchema])
async def get_companias(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Número de registros para saltar"),
    limit: int = Query(100, ge=1, le=100, description="Límite de registros a retornar"),
):
    """
    Obtiene todas las compañías con paginación
    """
    service = CompaniaService(db)
    companias = await service.get_companias(skip=skip, limit=limit)
    return companias

@router.post("/", response_model=CompaniaSchema, status_code=status.HTTP_201_CREATED)
async def create_compania(
    compania_in: CompaniaCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Crea una nueva compañía
    """
    service = CompaniaService(db)
    compania = await service.create_compania(compania_in=compania_in)
    return compania

@router.get("/{compania_id}", response_model=CompaniaWithRelations)
async def get_compania(
    compania_id: UUID4 = Path(..., description="ID de la compañía"),
    db: AsyncSession = Depends(get_db),
  ):
    """
    Obtiene una compañía por su ID
    """
    service = CompaniaService(db)
    compania = await service.get_compania(compania_id=compania_id)
    print(f"Compañía encontrada: {compania.__dict__}")
    return compania

@router.put("/{compania_id}", response_model=CompaniaSchema)
async def update_compania(
    compania_in: CompaniaUpdate,
    compania_id: UUID4 = Path(..., description="ID de la compañía"),
    db: AsyncSession = Depends(get_db),
    
):
    """
    Actualiza una compañía existente
    """
    service = CompaniaService(db)
    compania = await service.update_compania(
        compania_id=compania_id, compania_in=compania_in
    )
    return compania

@router.delete("/{compania_id}", response_model=CompaniaSchema)
async def delete_compania(
    compania_id: UUID4 = Path(..., description="ID de la compañía"),
    db: AsyncSession = Depends(get_db),
):
    """
    Elimina una compañía
    """
    service = CompaniaService(db)
    compania = await service.delete_compania(compania_id=compania_id)
    return compania

@router.get("/documento/{documento}", response_model=CompaniaSchema)
async def read_compania_by_documento(
    documento: str = Path(..., description="Documento de la compañía"),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene una compañía por su documento
    """
    service = CompaniaService(db)
    compania = await service.get_compania_by_documento(documento=documento)
    if not compania:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compañía con documento {documento} no encontrada"
        )
    return compania

@router.get("/tipo-documento/{tipo_documento_id}", response_model=List[CompaniaSchema])
async def read_companias_by_tipo_documento(
    tipo_documento_id: int = Path(..., description="ID del tipo de documento"),
    skip: int = Query(0, ge=0, description="Número de registros para saltar"),
    limit: int = Query(100, ge=1, le=100, description="Límite de registros a retornar"),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene todas las compañías por tipo de documento
    """
    service = CompaniaService(db)
    companias = await service.get_companias_by_tipo_documento(
        tipo_documento_id=tipo_documento_id, skip=skip, limit=limit
    )
    return companias 