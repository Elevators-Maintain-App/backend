from fastapi import APIRouter, Depends, Security
from typing import List
from app.schemas.comunes import LovElemento
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.rol import RolService
from app.services.compania import CompaniaService

router = APIRouter()

@router.get("/roles", response_model=List[LovElemento])
async def get_roles():
    service = RolService()
    return await service.get_roles("superAdmin")

@router.get("/companias", 
           response_model=List[LovElemento],)
async def get_companias(
    db: AsyncSession = Depends(get_db),
):
    service = CompaniaService(db)
    companias = await service.get_companias()
    return [LovElemento(id=compania.id, name=compania.nombre) for compania in companias]

