# app/api/routes/proyectos.py

from fastapi import APIRouter, Depends, status, HTTPException
from typing import List, Union
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.db.models.proyectos import Proyecto as ProyectoModel
from app.schemas.proyectos import ProyectoCreate, ProyectoUpdate, ProyectoInDBBase, CountOut, ProyectoCreateAdmin
from app.services.proyectos import ProyectoService
from app.auth.firebase import require_role

router = APIRouter()

# 1) superAdmin: count total de proyectos
@router.get(
    "/count",
    response_model=CountOut,
    status_code=status.HTTP_200_OK,
    summary="(superAdmin) Cuenta total de proyectos"
)
async def count_all_proyectos(
    user=Depends(require_role("superAdmin")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(func.count()).select_from(ProyectoModel))
    total: int = result.scalar_one()
    return {"count": total}

# 2) superAdmin: lista completa
@router.get(
    "/all",
    response_model=List[ProyectoInDBBase],
    status_code=status.HTTP_200_OK,
    summary="(superAdmin) Lista todos los proyectos"
)
async def list_all_proyectos(
    user=Depends(require_role("superAdmin")),
    db: AsyncSession = Depends(get_db)
):
    return await ProyectoService(db).get_all()

# 3) admin: count proyectos de su compañía
@router.get(
    "/company/count",
    response_model=CountOut,
    status_code=status.HTTP_200_OK,
    summary="(admin) Cuenta proyectos en su compañía"
)
async def count_company_proyectos(
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(func.count()).select_from(ProyectoModel).where(ProyectoModel.company_id == user.company_id)
    )
    total: int = result.scalar_one()
    return {"count": total}

# 4) admin: lista proyectos de su compañía
@router.get(
    "/company/all",
    response_model=List[ProyectoInDBBase],
    status_code=status.HTTP_200_OK,
    summary="(admin) Lista proyectos de su compañía"
)
async def list_company_proyectos(
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    return await ProyectoService(db).get_by_company(user.company_id)

@router.get(
    "/",
    response_model=List[ProyectoInDBBase]
)
async def get_proyectos(
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    return await ProyectoService(db).get_by_company(user.company_id)

@router.get(
    "/{proyecto_id}",
    response_model=ProyectoInDBBase
)
async def get_proyecto(
    proyecto_id: UUID,
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    return await ProyectoService(db).get_by_id_and_company(
        proyecto_id, user.company_id
    )

# 5) Post crear proyecto admin y superAdmin
@router.post(
    "/",
    response_model=ProyectoInDBBase,
    status_code=status.HTTP_201_CREATED,
    summary="Crear proyecto (admin o superAdmin)"
)
async def create_proyecto(
    proyecto_in: Union[ProyectoCreate, ProyectoCreateAdmin],
    user=Depends(require_role("admin", "superAdmin")),
    db: AsyncSession = Depends(get_db),
):
    """
    - **admin**: `company_id` se toma del token.
    - **superAdmin**: debe incluir `company_id` en el body.
    """
    # Determinar company_id segun rol
    if user.role == "admin":
        company_id = user.company_id
    else:  # superAdmin
        # Validar que venga company_id en el tipo correcto
        if not isinstance(proyecto_in, ProyectoCreateAdmin):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Los superAdmin deben enviar company_id en la petición"
            )
        company_id = proyecto_in.company_id

    # Crear el proyecto
    return await ProyectoService(db).create(proyecto_in, company_id=company_id)

@router.put(
    "/{proyecto_id}",
    response_model=ProyectoInDBBase
)
async def update_proyecto(
    proyecto_id: UUID,
    proyecto_in: ProyectoUpdate,
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    return await ProyectoService(db).update(proyecto_id, proyecto_in, company_id=user.company_id)

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
