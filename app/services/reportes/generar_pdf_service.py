# # app/services/reportes/generar_pdf_service,py

# from jinja2 import Environment, FileSystemLoader
# from weasyprint import HTML
# import io
# from app.services.firebase_storage.firebase_storage import subir_pdf_a_storage
# from app.services.checklists import ChecklistService
# from app.db.models.checklists import Checklist
# from sqlalchemy.ext.asyncio import AsyncSession

# async def generar_y_subir_pdf(orden_id, db: AsyncSession, tipo: str = "prereporte") -> str:
#     checklist = await ChecklistService(db).get_checklist_con_items(orden_id)
#     if not checklist:
#         raise ValueError("Checklist no encontrado")

#     env = Environment(loader=FileSystemLoader("app/templates"))
#     template = env.get_template("reporte_checklist.html")
#     html_content = template.render(checklist=checklist)

#     pdf_buffer = io.BytesIO()
#     HTML(string=html_content, base_url=".").write_pdf(pdf_buffer)
#     pdf_buffer.seek(0)

#     url = subir_pdf_a_storage(pdf_buffer.read(), orden_id, tipo)

#     # Guardar URL en base de datos
#     if tipo == "prereporte":
#         checklist.reporte_prerevision_url = url
#     else:
#         checklist.reporte_final_url = url

#     await db.commit()

#     return url

# app/services/reportes/generar_pdf_service.py

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import io
from datetime import timezone
from app.services.firebase_storage.firebase_storage import subir_pdf_a_storage
from app.services.checklists import ChecklistService
from app.db.models.seguimiento import OrdenTrabajoSeguimiento, EventoOrden
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

LOCAL_TZ = None  # si quieres, puedes usar zoneinfo("America/Panama")

async def _geo_por_item(db: AsyncSession, checklist_item_ids):
    """
    Retorna {item_id: {"lat": float, "lon": float, "timestamp": datetime_tzaware}} 
    tomando el seguimiento más reciente con evento PASO_COMPLETADO.
    """
    if not checklist_item_ids:
        return {}

    # Trae todos los seguimientos de esos items con evento PASO_COMPLETADO
    stmt = (
        select(OrdenTrabajoSeguimiento)
        .where(
            OrdenTrabajoSeguimiento.checklist_item_id.in_(list(checklist_item_ids)),
            OrdenTrabajoSeguimiento.evento == EventoOrden.PASO_COMPLETADO,
        )
        .order_by(desc(OrdenTrabajoSeguimiento.timestamp))
    )
    res = await db.execute(stmt)
    rows = res.scalars().all()

    geo = {}
    # nos quedamos con el más reciente por item_id
    for seg in rows:
        iid = seg.checklist_item_id
        if iid not in geo and seg.lat is not None and seg.lon is not None:
            ts = seg.timestamp
            # Normalizar tz (asegúrate que timestamp viene tz-aware del DB)
            if ts and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            geo[iid] = {"lat": seg.lat, "lon": seg.lon, "timestamp": ts}
    return geo

async def generar_y_subir_pdf(orden_id, db: AsyncSession, tipo: str = "prereporte") -> str:
    # ⚠️ IMPORTANTE: si llamas esta función en background, evita reutilizar 'db' del request.
    # Idealmente crea un nuevo session dentro de esta función usando sessionmaker.
    # Aquí asumo que 'db' sigue válido. Si notas errores intermitentes, migra a session propio.

    checklist = await ChecklistService(db).get_checklist_con_items(orden_id)
    if not checklist:
        raise ValueError("Checklist no encontrado")

    # Recolectar IDs de items
    item_ids = [it.id for it in checklist.items or []]
    geo = await _geo_por_item(db, item_ids)

    # Preparar items enriquecidos para el template
    items_enriquecidos = []
    for it in sorted(checklist.items, key=lambda x: x.step_number):
        meta = geo.get(it.id)
        items_enriquecidos.append({
            "id": it.id,
            "step_number": it.step_number,
            "titulo": it.titulo,
            "instrucciones": it.instrucciones,
            "comentario": it.comentario,
            "evidencia_data": it.evidencia_data or {},
            "seguimiento": meta,  # dict con lat/lon/timestamp o None
        })

    env = Environment(loader=FileSystemLoader("app/templates"))
    template = env.get_template("reporte_checklist.html")
    html_content = template.render(checklist=checklist, items=items_enriquecidos)

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
