# # app/api/routes/checklists.py

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.checklists import (
    ChecklistTemplateOut, ChecklistOut,
    ChecklistItemUpdate, ChecklistTemplateCreate,
    ChecklistTemplateOut2
)
from app.services.checklists import ChecklistService
from app.auth.firebase import require_role, get_current_firebase_user


from fastapi.responses import StreamingResponse
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
import io

router = APIRouter()

@router.get(
    "/{orden_id}/template",
    response_model=ChecklistTemplateOut,
    summary="(technician) Obtener plantilla de checklist para la orden"
)
async def get_template(
    orden_id: UUID = Path(...),
    user=Depends(require_role("technician")),
    db: AsyncSession = Depends(get_db)
):
    svc = ChecklistService(db)
    return await svc.get_template_for_order(orden_id)

@router.get(
    "/{orden_id}/load",
    status_code=201,
    summary="(technician) inicializar checklist de la orden"
)
async def load_checklist(
    orden_id: UUID = Path(...),
    user=Depends(require_role("technician", "supervisor")),
    db: AsyncSession = Depends(get_db)
):
    svc = ChecklistService(db)
    try:
        await svc.init_checklist(orden_id)
        return {"message": "Checklist inicializado exitosamente"}
    except HTTPException as e:
        raise e  
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

@router.get(
    "/{orden_id}",
    response_model=ChecklistOut,
    summary="(technician) Obtener o inicializar checklist de la orden"
)
async def get_checklist(
    orden_id: UUID = Path(...),
    user=Depends(require_role("technician", "supervisor")),
    db: AsyncSession = Depends(get_db)
):
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
    user=Depends(require_role("technician", "supervisor")),
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
    response_model=ChecklistTemplateOut2,
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

@router.get("/{orden_id}/reporte.pdf")
async def generar_reporte_pdf(
    orden_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    checklist = await ChecklistService(db).get_checklist_con_items(orden_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist no encontrado")

    # Renderizar HTML
    env = Environment(loader=FileSystemLoader("app/templates"))
    template = env.get_template("reporte_checklist.html")
    html_content = template.render(checklist=checklist)

    # Generar PDF
    pdf_buffer = io.BytesIO()
    HTML(string=html_content, base_url=".").write_pdf(pdf_buffer)
    pdf_buffer.seek(0)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=reporte_{orden_id}.pdf"}
    )