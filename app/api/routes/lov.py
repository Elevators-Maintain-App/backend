from fastapi import APIRouter, Depends, Security
from typing import List
from app.schemas.comunes import LovElemento
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.usuario.rol import RolService
from app.services.compania import CompaniaService
from app.services.usuario.nivel_tecnico import NivelTecnicoService
from app.services.secundarios.pais import PaisService
from app.auth.firebase import require_role

router = APIRouter()

@router.get("/roles", response_model=List[LovElemento])
async def get_roles():
    service = RolService()
    return await service.get_roles("superAdmin")

@router.get("/companias",
           response_model=List[LovElemento],)
async def get_companias(
    db: AsyncSession = Depends(get_db),
    usuario_actual=Depends(require_role("superAdmin")),
):
    service = CompaniaService(db)
    companias = await service.get_companias(usuario_actual=usuario_actual)
    return [LovElemento(id=compania.id, name=compania.nombre) for compania in companias]

@router.get("/niveles-tecnicos", 
           response_model=List[LovElemento],)
async def get_nivel_tecnico(
    db: AsyncSession = Depends(get_db),
):
    service = NivelTecnicoService(db)
    niveles_tecnicos = await service.get_niveles_tecnicos()
    return [LovElemento(id=nivel_tecnico.id, name=nivel_tecnico.nombre) for nivel_tecnico in niveles_tecnicos]

@router.get("/paises", 
           response_model=List[LovElemento],)
async def get_paises(
    db: AsyncSession = Depends(get_db),
):
    service = PaisService(db)
    paises = await service.get_paises()
    return [LovElemento(id=pais.id, name=pais.nombre) for pais in paises]

