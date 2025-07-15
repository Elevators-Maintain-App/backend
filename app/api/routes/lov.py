from fastapi import APIRouter, Depends, Security
from typing import List
from app.schemas.comunes import LovElemento
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.usuario.rol import RolService
from app.services.compania import CompaniaService
from app.services.usuario.nivel_tecnico import NivelTecnicoService
from app.services.secundarios.pais import PaisService
from app.auth.firebase import require_role, get_current_firebase_user
from app.db.repositories.tipos_documento import tipo_documento_crud
from app.services.cliente import ClienteService
from app.services.proyectos import ProyectoService

router = APIRouter()

@router.get("/roles", response_model=List[LovElemento])
async def get_roles(
    usuario_actual=Depends(get_current_firebase_user)
):
    service = RolService()
    return await service.get_roles(usuario_actual.rol)

@router.get("/companias",
           response_model=List[LovElemento],)
async def get_companias(
    db: AsyncSession = Depends(get_db),
    usuario_actual=Depends(require_role("superAdmin")),
):
    service = CompaniaService(db)
    companias_paginadas = await service.get_companias_con_paginacion(usuario_actual=usuario_actual)
    return [LovElemento(id=compania.id, name=compania.nombre) for compania in companias_paginadas.data]

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

@router.get("/tipos-documento", 
           response_model=List[LovElemento],)
async def get_tipos_documento(
    db: AsyncSession = Depends(get_db),
):
    tipos_documento = await tipo_documento_crud.get_multi(db)
    return [LovElemento(id=tipo_documento.id, name=tipo_documento.nombre) for tipo_documento in tipos_documento]

@router.get("/clientes",
           response_model=List[LovElemento],) 
async def get_clientes(
    db: AsyncSession = Depends(get_db),
    usuario_actual=Depends(require_role("superAdmin", "admin", "supervisor")),
):
    service = ClienteService(db)
    clientes = await service.get_clientes_con_paginacion(usuario_actual=usuario_actual, limit=1000, skip=0)
    return [LovElemento(id=cliente.id, name=cliente.nombre) for cliente in clientes.data]

@router.get("/proyectos", response_model=List[LovElemento])
async def get_proyectos(
    db: AsyncSession = Depends(get_db),
    usuario_actual=Depends(require_role("superAdmin", "admin", "supervisor")),
):
    service = ProyectoService(db)
    # 1000 es suficiente para autocompletados; ajusta si lo necesitas
    proyectos = await service.get_proyectos_con_paginacion(
        usuario_actual=usuario_actual,
        limit=1000,
        skip=0
    )
    return [LovElemento(id=p.id, name=p.nombre) for p in proyectos.data]