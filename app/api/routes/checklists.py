# # app/api/routes/checklists.py

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.checklists import (
    ChecklistTemplateOut, ChecklistOut,
    ChecklistItemUpdate, ChecklistTemplateCreate
)
from app.services.checklists import ChecklistService
from app.auth.firebase import require_role, get_current_firebase_user

router = APIRouter()

@router.get(
    "/{orden_id}/template",
    response_model=ChecklistTemplateOut,
    summary="(technician) Obtener plantilla de checklist para la orden"
)
async def get_template(
    orden_id: UUID = Path(...),
    user=Depends(get_current_firebase_user),
    db: AsyncSession = Depends(get_db)
):
    if user.role != "technician":
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    svc = ChecklistService(db)
    return await svc.get_template_for_order(orden_id)

@router.get(
    "/{orden_id}",
    response_model=ChecklistOut,
    summary="(technician) Obtener o inicializar checklist de la orden"
)
async def get_checklist(
    orden_id: UUID = Path(...),
    user=Depends(get_current_firebase_user),
    db: AsyncSession = Depends(get_db)
):
    if user.role != "technician":
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    svc = ChecklistService(db)
    return await svc.get_checklist(orden_id)

@router.patch(
    "/{orden_id}/items/{step_number}",
    response_model=ChecklistItemUpdate,
    summary="(technician) Actualizar paso de checklist"
)
async def update_checklist_item(
    orden_id: UUID      = Path(...),
    step_number: int    = Path(..., gt=0),
    data: ChecklistItemUpdate = Body(...),
    user=Depends(require_role("technician")),
    db: AsyncSession = Depends(get_db)
):
    svc = ChecklistService(db)
    return await svc.update_item(
        orden_id=orden_id,
        step_number=step_number,
        evidencia_data=data.evidencia_data,
        comentario=data.comentario,
        confirm=data.confirm
    )

@router.post(
    "/templates",
    response_model=ChecklistTemplateOut,
    status_code=status.HTTP_201_CREATED,
    summary="(admin) Crear plantilla de checklist con pasos"
)
async def create_template(
    payload: ChecklistTemplateCreate,
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Crea una nueva plantilla de checklist y todos sus pasos (items) asociados.
    Solo usuarios con rol 'admin' pueden acceder.
    """
    svc = ChecklistService(db)
    return await svc.create_template_with_items(payload)