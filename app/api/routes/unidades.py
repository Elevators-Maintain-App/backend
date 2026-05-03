# app/api/routes/unidades.py

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.db.models.unidades import Unidad as UnidadModel
from app.db.models.proyectos import Proyecto as ProyectoModel
from app.db.models.clientes import Cliente as ClienteModel
from app.db.models.enums.tipos_unidad import TipoUnidad as TipoUnidadModel
from app.schemas.unidades import (
    UnidadCreate,
    UnidadUpdate,
    UnidadInDBBase,
    UnidadListOut
)
from app.schemas.proyectos import CountOut
from app.services.unidades import UnidadService
from app.auth.firebase import require_role, get_firestore_client

router = APIRouter()

async def _map_unidad(
    unidad: UnidadModel,
    db: AsyncSession
) -> UnidadListOut:
    # 1. Nombre de proyecto
    proyecto = await db.get(ProyectoModel, unidad.proyecto_id)
    proyecto_nombre = proyecto.nombre if proyecto else "—"

    # 2. Nombre de cliente
    cliente = await db.get(ClienteModel, proyecto.cliente_id)
    cliente_nombre = cliente.nombre if cliente else "—"

    # Nombre de tipo de unidad
    tipo = await db.get(TipoUnidadModel, unidad.tipo_unidad_id)
    tipo_nombre = tipo.nombre if tipo else "—"

    return UnidadListOut(
        id=unidad.id,
        nombre=unidad.nombre,
        kpi_funcionamiento=unidad.kpi_funcionamiento,
        proyecto=proyecto_nombre,
        cliente=cliente_nombre,
        tipo_unidad_id=unidad.tipo_unidad_id,
        tipo_unidad=tipo_nombre, 
        company_id=unidad.company_id,
        created_at=unidad.created_at,
        updated_at=unidad.updated_at
    )

# 1) Contar unidades de la compañía (admin)
@router.get(
    "/company/count",
    response_model=CountOut,
    status_code=status.HTTP_200_OK,
    summary="(admin) Cuenta unidades en su compañía"
)
async def count_company_unidades(
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(func.count()).select_from(UnidadModel)
        .where(UnidadModel.company_id == user.company_id)
    )
    total: int = result.scalar_one()
    return {"count": total}


# 2) Listar unidades de la compañía (admin)
@router.get(
    "/company/all",
    response_model=List[UnidadListOut],
    status_code=status.HTTP_200_OK,
    summary="(admin) Lista unidades de su compañía"
)
async def list_company_unidades(
    user=Depends(require_role("admin", "supervisor")),
    db: AsyncSession = Depends(get_db)
):
    return await UnidadService(db).list_company_unidades_out(user.company_id)


# 3) Obtener detalle de una unidad (admin)
@router.get(
    "/{unidad_id}",
    response_model=UnidadListOut,
    status_code=status.HTTP_200_OK,
    summary="(admin) Detalle de una unidad"
)
async def get_unidad_detail(
    unidad_id: UUID = Path(..., description="ID de la unidad"),
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    unidad = await UnidadService(db).get_by_id_and_company(unidad_id, user.company_id)
    return await _map_unidad(unidad, db)


# 4) Crear unidad (admin)
@router.post(
    "/",
    response_model=UnidadInDBBase,
    status_code=status.HTTP_201_CREATED,
    summary="(admin) Crear una nueva unidad"
)
async def create_unidad(
    unidad_in: UnidadCreate,
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    return await UnidadService(db).create(unidad_in, user.company_id)


# 5) Actualizar unidad (admin)
@router.put(
    "/{unidad_id}",
    response_model=UnidadInDBBase,
    status_code=status.HTTP_200_OK,
    summary="(admin) Actualizar una unidad"
)
async def update_unidad(
    unidad_in: UnidadUpdate,
    unidad_id: UUID = Path(..., description="ID de la unidad"),
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    return await UnidadService(db).update(unidad_id, unidad_in, user.company_id)


# 6) Eliminar unidad (admin)
@router.delete(
    "/{unidad_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="(admin) Eliminar una unidad"
)
async def delete_unidad(
    unidad_id: UUID = Path(..., description="ID de la unidad"),
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    await UnidadService(db).delete(unidad_id, user.company_id)


async def enrich_unidad_with_cliente_info(unidad: UnidadModel) -> UnidadListOut:
    """Helper function to enrich unidad with cliente information from Firebase"""
    cliente_nombre = "Cliente no encontrado"
    cliente_email = "No disponible"
    
    if unidad.proyecto and unidad.proyecto.cliente_id:
        doc = get_firestore_client().collection("users").document(unidad.proyecto.cliente_id).get()
        if doc.exists:
            data = doc.to_dict()
            cliente_nombre = data.get("display_name", "Cliente no encontrado")
            cliente_email = data.get("email", "No disponible")
    
    return UnidadListOut(
        id=unidad.id,
        nombre=unidad.nombre,
        kpi_funcionamiento=unidad.kpi_funcionamiento,
        proyecto=unidad.proyecto.nombre if unidad.proyecto else None,
        cliente=cliente_nombre,
        tipo_unidad_id=unidad.tipo_unidad_id,
        tipo_unidad=unidad.tipo_unidad.nombre if unidad.tipo_unidad else None,
        company_id=unidad.company_id,
        cliente_id=unidad.proyecto.cliente_id if unidad.proyecto else None,
        cliente_email=cliente_email,
        created_at=unidad.created_at,
        updated_at=unidad.updated_at
    )
