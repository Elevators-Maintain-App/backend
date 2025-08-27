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

def _resolve_attr_chain(obj, chain: str):
    """Intenta resolver 'a.b.c' de forma segura; retorna None si no existe."""
    cur = obj
    for part in chain.split("."):
        if cur is None:
            return None
        cur = getattr(cur, part, None)
    return cur

def _pick_first(*vals):
    """Primer valor truthy (no None, no '') o None."""
    for v in vals:
        if v:
            return v
    return None

async def generar_y_subir_pdf(orden_id, db: AsyncSession, tipo: str = "prereporte") -> str:
    checklist = await ChecklistService(db).get_checklist_con_items(orden_id)
    if not checklist:
        raise ValueError("Checklist no encontrado")

    # Items enriquecidos (como ya lo tienes)
    item_ids = [it.id for it in checklist.items or []]
    geo = await _geo_por_item(db, item_ids)
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
            "seguimiento": meta,
        })

    # ---- Cabecera extendida ----
    odt = getattr(checklist, "orden_de_trabajo", None)
    cabecera = {
        "tecnico": _pick_first(
            _resolve_attr_chain(odt, "tecnico_asignado.nombre"),
            _resolve_attr_chain(odt, "tecnico.nombre"),
            getattr(odt, "tecnico_asignado", None),  # si ya es string
            getattr(odt, "tecnico", None),
            (checklist.check_metadata or {}).get("tecnico")
        ),
        "supervisor": _pick_first(
            _resolve_attr_chain(odt, "supervisor_asignado.nombre"),
            _resolve_attr_chain(odt, "supervisor.nombre"),
            getattr(odt, "supervisor_asignado", None),
            getattr(odt, "supervisor", None),
            (checklist.check_metadata or {}).get("supervisor")
        ),
        "proyecto": _pick_first(
            _resolve_attr_chain(odt, "proyecto.nombre"),
            getattr(odt, "proyecto", None),
            (checklist.check_metadata or {}).get("proyecto")
        ),
        "unidad": _pick_first(
            _resolve_attr_chain(odt, "unidad.codigo"),
            _resolve_attr_chain(odt, "unidad.nombre"),
            getattr(odt, "unidad", None),
            (checklist.check_metadata or {}).get("unidad")
        ),
        "cliente": _pick_first(
            _resolve_attr_chain(odt, "cliente.razon_social"),
            _resolve_attr_chain(odt, "cliente.nombre"),
            getattr(odt, "cliente", None),
            (checklist.check_metadata or {}).get("cliente")
        ),
    }

    # ---- Branding (logo) ----
    # Ajusta estas variables a tus rutas reales o a configuración
    branding = {
        "logo_url": "app/templates/logo.png",
        "logo_w": 100,  # px (ajustable)
        "logo_h": 60,   # px (ajustable)
    }

    env = Environment(loader=FileSystemLoader("app/templates"))
    template = env.get_template("reporte_checklist.html")
    html_content = template.render(
        checklist=checklist,
        items=items_enriquecidos,
        cabecera=cabecera,
        branding=branding,
    )

    pdf_buffer = io.BytesIO()
    HTML(string=html_content, base_url=".").write_pdf(pdf_buffer)
    pdf_buffer.seek(0)

    url = subir_pdf_a_storage(pdf_buffer.read(), orden_id, tipo)

    if tipo == "prereporte":
        checklist.reporte_prerevision_url = url
    else:
        checklist.reporte_final_url = url

    await db.commit()
    return url
