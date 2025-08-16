# app/services/reportes/generar_pdf_service,py

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import io
from app.services.firebase_storage.firebase_storage import subir_pdf_a_storage
from app.services.checklists import ChecklistService
from app.db.models.checklists import Checklist
from sqlalchemy.ext.asyncio import AsyncSession

async def generar_y_subir_pdf(orden_id, db: AsyncSession, tipo: str = "prereporte") -> str:
    checklist = await ChecklistService(db).get_checklist_con_items(orden_id)
    if not checklist:
        raise ValueError("Checklist no encontrado")

    env = Environment(loader=FileSystemLoader("app/templates"))
    template = env.get_template("reporte_checklist.html")
    html_content = template.render(checklist=checklist)

    pdf_buffer = io.BytesIO()
    HTML(string=html_content, base_url=".").write_pdf(pdf_buffer)
    pdf_buffer.seek(0)

    url = subir_pdf_a_storage(pdf_buffer.read(), orden_id, tipo)

    # Guardar URL en base de datos
    if tipo == "prereporte":
        checklist.reporte_prerevision_url = url
    else:
        checklist.reporte_final_url = url

    await db.commit()

    return url