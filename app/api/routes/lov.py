from fastapi import APIRouter, Depends, Security, Query
from typing import List, Optional
from uuid import UUID
from app.schemas.comunes import LovElemento, PaginacionResponse
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.usuario.rol import RolService
from app.services.compania import CompaniaService
from app.services.usuario.nivel_tecnico import NivelTecnicoService
from app.services.secundarios.pais import PaisService
from app.auth.firebase import require_role, get_current_firebase_user
from app.db.repositories.tipos_documento import tipo_documento_crud
from app.db.repositories.tipos_unidad import tipo_unidad_crud
from app.db.repositories.prioridades import prioridad_crud
from app.db.repositories.tipos_orden import tipo_orden_crud
from app.services.cliente import ClienteService
from app.services.proyectos.proyectos import ProyectoService
from app.services.unidades import UnidadService
from app.services.tecnico import TecnicoService
from app.services.supervisor import SupervisorService

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

@router.get("/tipos-unidad", 
           response_model=List[LovElemento],)
async def get_tipos_unidad(
    db: AsyncSession = Depends(get_db),
):
    tipos_unidad = await tipo_unidad_crud.get_multi(db)
    return [LovElemento(id=tipo_unidad.id, name=tipo_unidad.nombre) for tipo_unidad in tipos_unidad]

@router.get("/prioridades", 
           response_model=List[LovElemento],)
async def get_prioridades(
    db: AsyncSession = Depends(get_db),
):
    prioridades = await prioridad_crud.get_multi(db)
    return [LovElemento(id=prioridad.id, name=prioridad.nombre) for prioridad in prioridades]

@router.get("/tipos-orden", 
           response_model=PaginacionResponse[LovElemento],)
async def get_tipos_orden(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Número de registros para saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
):
    tipos_orden = await tipo_orden_crud.get_multi(db, skip=skip, limit=limit)
    total = await tipo_orden_crud.get_total_with_advanced_filters(db)
    return PaginacionResponse(
        data=[LovElemento(id=tipo_orden.id, name=tipo_orden.nombre) for tipo_orden in tipos_orden],
        total=total,
        skip=skip,
        limit=limit
    )

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
    proyectos = await service.get_proyectos_con_paginacion(
        usuario_actual=usuario_actual,
        limit=1000,
        skip=0
    )
    return [LovElemento(id=p.id, name=p.nombre) for p in proyectos.data]

@router.get("/unidades", response_model=List[LovElemento])
async def get_unidades(
    db: AsyncSession = Depends(get_db),
    usuario_actual=Depends(require_role("superAdmin", "admin", "supervisor")),
    proyecto_id: Optional[UUID] = Query(None, alias="proyecto_id"),
):
    service = UnidadService(db)
    unidades = await service.get_unidades_con_paginacion(
        usuario_actual=usuario_actual,
        proyecto_id=proyecto_id,
        limit=1000,
        skip=0
    )
    return [LovElemento(id=u.id, name=u.nombre) for u in unidades.data]

@router.get("/tecnicos", response_model=List[LovElemento])
async def get_tecnicos(
    db: AsyncSession = Depends(get_db),
    usuario_actual=Depends(require_role("superAdmin", "admin", "supervisor")),
):
    service = TecnicoService(db)
    tecnicos = await service.get_tecnicos_con_paginacion(
        usuario_actual=usuario_actual,
        limit=1000,
        skip=0
    )
    return [LovElemento(id=t.uid, name=t.display_name) for t in tecnicos.data]

@router.get("/supervisores", response_model=List[LovElemento])
async def get_supervisores(
    db: AsyncSession = Depends(get_db),
    usuario_actual=Depends(require_role("superAdmin", "admin", "supervisor")),
):
    service = SupervisorService(db)
    supervisores = await service.get_supervisores_con_paginacion(
        usuario_actual=usuario_actual,
        limit=1000,
        skip=0
    )
    return [LovElemento(id=s.uid, name=s.display_name) for s in supervisores.data]

