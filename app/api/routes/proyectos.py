# app/api/routes/proyectos.py

from fastapi import APIRouter, Depends, status, HTTPException, Path
from typing import List, Union
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.db.models.proyectos import Proyecto as ProyectoModel
from app.schemas.proyectos import ProyectoCreate, ProyectoUpdate, ProyectoInDBBase, CountOut, ProyectoDetailOut, ProyectoListOut
from app.services.proyectos import ProyectoService
from app.auth.firebase import require_role, get_firestore_client
from app.db.repositories.zonas_geograficas import zona_geografica_crud
from app.db.models.compania import Compania as CompaniaModel

router = APIRouter()

async def _map_to_list_out(
    proyecto: ProyectoInDBBase,
    db: AsyncSession
) -> ProyectoListOut:
    # 1) zona
    zona = None
    if proyecto.zona_geografica_id:
        z = await zona_geografica_crud.get(db, proyecto.zona_geografica_id)
        zona = z.nombre if z else None

    # 2) compañía
    comp = await db.get(CompaniaModel, proyecto.company_id)
    compania = comp.nombre if comp else "—"

    # 3) cliente
    doc = get_firestore_client().collection("users").document(proyecto.cliente_id).get()
    cliente = doc.to_dict().get("display_name", "—") if doc.exists else "—"

    return ProyectoListOut(
        id=proyecto.id,
        nombre=proyecto.nombre,
        direccion=proyecto.direccion,
        zona_geografica=zona,
        cliente=cliente,
        compania=compania
    )

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
    response_model=List[ProyectoListOut],
    status_code=status.HTTP_200_OK,
    summary="(superAdmin) Lista todos los proyectos"
)
async def list_all_proyectos(
    user=Depends(require_role("superAdmin")),
    db: AsyncSession = Depends(get_db)
):
    proyectos = await ProyectoService(db).get_all()
    return [await _map_to_list_out(p, db) for p in proyectos]

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
    response_model=List[ProyectoListOut],
    status_code=status.HTTP_200_OK,
    summary="(admin) Lista proyectos de su compañía"
)
async def list_company_proyectos(
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    proyectos = await ProyectoService(db).get_by_company(user.company_id)
    return [await _map_to_list_out(p, db) for p in proyectos]

@router.get(
    "/",
    response_model=List[ProyectoInDBBase],
    status_code=status.HTTP_200_OK
)
async def get_proyectos(
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    return await ProyectoService(db).get_by_company(user.company_id)

@router.get(
    "/{proyecto_id}",
    response_model=ProyectoDetailOut,
    status_code=status.HTTP_200_OK,
    summary="Detalle de un proyecto (admin o superAdmin)"
)
async def get_proyecto_detail(
    proyecto_id: UUID = Path(..., description="ID del proyecto"),
    user=Depends(require_role("admin", "superAdmin")),
    db: AsyncSession = Depends(get_db),
):
    # 1. Obtener proyecto y validar permisos
    proyecto = await ProyectoService(db).get_by_id(proyecto_id)

    # 2. Nombre de zona
    zona = None
    if proyecto.zona_geografica_id:
        z = await zona_geografica_crud.get(db, proyecto.zona_geografica_id)
        zona = z.nombre if z else None

    # 3. Nombre de compañía
    comp = await db.get(CompaniaModel, proyecto.company_id)
    nombre_compania = comp.nombre if comp else "—"

    # 4. Nombre de cliente (Firestore)
    doc = get_firestore_client().collection("users").document(proyecto.cliente_id).get()
    if not doc.exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado en Firebase")
    cliente_name = doc.to_dict().get("display_name", "—")

    return ProyectoDetailOut(
        id=proyecto.id,
        nombre=proyecto.nombre,
        direccion=proyecto.direccion,
        zona_geografica=zona,
        cliente=cliente_name,
        compania=nombre_compania,
        created_at=proyecto.created_at,
        updated_at=proyecto.updated_at,
    )

# 5) Post crear proyecto admin y superAdmin
@router.post(
    "/",
    response_model=ProyectoInDBBase,
    status_code=status.HTTP_201_CREATED,
    summary="Crear proyecto (admin o superAdmin)"
)
async def create_proyecto(
    proyecto_in: ProyectoCreate,
    user=Depends(require_role("admin", "superAdmin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea un proyecto asignándolo automáticamente a la compañía
    asociada al cliente indicado en `cliente_id`.
    """
    # 1) Obtener cliente de Firestore
    doc = get_firestore_client().collection("users").document(proyecto_in.cliente_id).get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente {proyecto_in.cliente_id} no encontrado"
        )
    data = doc.to_dict()
    company_uid = data.get("company_id")
    if not company_uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El cliente no está vinculado a ninguna compañía"
        )

    # 2) Validar que el requester (si es admin) solo cree en su propia compañía
    if user.role == "admin" and str(user.company_id) != company_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes crear proyectos en otra compañía"
        )

    # 3) Crear proyecto con company_id obtenido de Firestore
    return await ProyectoService(db).create(
        proyecto_in,
        company_id=UUID(company_uid)
    )

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
