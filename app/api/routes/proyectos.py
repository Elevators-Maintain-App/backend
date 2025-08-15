# app/api/routes/proyectos.py

from fastapi import APIRouter, Depends, status, Path, Query
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.proyectos import ProyectoCreate, ProyectoUpdate, ProyectoDetailOut, ProyectoOut
from app.services.proyectos.proyectos import ProyectoService
from app.auth.firebase import require_role,  FirebaseUser

from app.schemas.comunes import PaginacionResponse
from app.services.proyectos.proyectos_mappers import map_proyecto_to_proyecto_out

router = APIRouter()

@router.get(
    "/",
    response_model=PaginacionResponse[ProyectoOut],
    status_code=status.HTTP_200_OK,
    summary="Lista de proyectos con paginación y filtros por rol"
)
async def get_proyectos(
    db: AsyncSession = Depends(get_db),
    usuario_actual: FirebaseUser = Depends(require_role("superAdmin", "admin", "supervisor")),
    skip: int = Query(0, ge=0, description="Número de registros para saltar"),
    limit: int = Query(20, ge=1, le=100, description="Límite de registros a retornar"),
    search: Optional[str] = Query(None, description="Buscar por nombre"),
    company_id: Optional[str] = Query(None, description="ID de la compañía"),
    cliente_id: Optional[str] = Query(None, description="ID del cliente")
):
    return await ProyectoService(db).get_proyectos_con_paginacion(
        usuario_actual=usuario_actual,
        skip=skip,
        limit=limit,
        search=search,
        company_id=company_id,
        cliente_id=cliente_id
    )

@router.get(
    "/{proyecto_id}",
    response_model=ProyectoDetailOut,
    status_code=status.HTTP_200_OK,
    summary="Detalle de un proyecto"
)
async def get_proyecto_detail(
    proyecto_id: UUID = Path(..., description="ID del proyecto"),
    user=Depends(require_role("admin", "superAdmin", "supervisor")),
    db: AsyncSession = Depends(get_db),
):
    proyecto = await ProyectoService(db).get_by_id(proyecto_id)
    proyecto_out = map_proyecto_to_proyecto_out(proyecto)

    return proyecto_out

@router.post(
    "/",
    response_model=ProyectoDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear proyecto "
)
async def create_proyecto(
    proyecto_in: ProyectoCreate,
    user=Depends(require_role("admin", "superAdmin")),
    db: AsyncSession = Depends(get_db),
):
    return await ProyectoService(db).create(proyecto_in, user)

@router.put(
    "/{proyecto_id}",
    response_model=ProyectoDetailOut
)
async def update_proyecto(
    proyecto_id: UUID,
    proyecto_in: ProyectoUpdate,
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    proyecto = await ProyectoService(db).update(proyecto_id, proyecto_in, user)
    return map_proyecto_to_proyecto_out(proyecto)

@router.delete(
    "/{proyecto_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_proyecto(
    proyecto_id: UUID,
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    await ProyectoService(db).delete(proyecto_id, company_id=user.company_id)
