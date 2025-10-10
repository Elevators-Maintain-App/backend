# app/services/reportes/generar_pdf_service.py

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import io
from datetime import timezone
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal   
from app.services.firebase_storage.firebase_storage import subir_pdf_a_storage
from app.services.checklists import ChecklistService
from app.db.models.seguimiento import OrdenTrabajoSeguimiento, EventoOrden
from app.db.models.checklists import Checklist
from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.db.models.usuarios import Usuario
from app.db.models.clientes import Cliente
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("America/Panama") 

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

async def generar_y_subir_pdf(orden_id, tipo: str = "prereporte") -> str:
    # ← sesión propia para el background task
    async with AsyncSessionLocal() as db:
        # EAGER LOAD del checklist con items y orden_de_trabajo (+ subrelaciones si las usas)
        checklist = await db.scalar(
            select(Checklist)
            .options(
                selectinload(Checklist.items),
                # Orden y sub-relaciones que SÍ existen en tu modelo
                selectinload(Checklist.orden_de_trabajo)
                    .selectinload(OrdenDeTrabajo.unidad),
                selectinload(Checklist.orden_de_trabajo)
                    .selectinload(OrdenDeTrabajo.compania),
                selectinload(Checklist.orden_de_trabajo)
                    .selectinload(OrdenDeTrabajo.tipo_orden),
                selectinload(Checklist.orden_de_trabajo)
                    .selectinload(OrdenDeTrabajo.estado),
                selectinload(Checklist.orden_de_trabajo)
                    .selectinload(OrdenDeTrabajo.prioridad),
                # cliente y tecnico ya están configurados con lazy="joined" en el modelo,
                # por lo que se cargan al traer OrdenDeTrabajo. No hace falta selectinload.
            )
            .where(Checklist.orden_trabajo_id == orden_id)
        )
        if not checklist:
            raise ValueError("Checklist no encontrado")

        # Items enriquecidos
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

        # Cabecera extendida (sin awaitable_attrs porque ya hicimos eager-load)
        odt = getattr(checklist, "orden_de_trabajo", None)

        # Resolver nombre del supervisor (no hay relación; buscamos en Usuario por uid)
        supervisor_nombre = None
        if odt and getattr(odt, "supervisor_id", None):
            sup = await db.scalar(select(Usuario).where(Usuario.uid == odt.supervisor_id))
            if sup:
                supervisor_nombre = (
                    getattr(sup, "nombre", None)
                    or getattr(sup, "display_name", None)
                    or odt.supervisor_id
                )

        cliente_nombre = None
        if odt and getattr(odt, "cliente_id", None):
            cli = await db.scalar(select(Cliente).where(Cliente.id == odt.cliente_id))
            if cli:
                cliente_nombre = (
                    getattr(cli, "nombre", None)
                    or getattr(cli, "display_name", None)
                    or odt.cliente_id
                )

        cabecera = {
            # Mostrar el consecutivo si existe; si no, cae al UUID
            "orden_ref": _pick_first(getattr(odt, "referencia", None)),
            "orden_id": getattr(odt, "id", None),

            "tecnico": _pick_first(
                _resolve_attr_chain(odt, "tecnico.nombre"),
                _resolve_attr_chain(odt, "tecnico.display_name"),
                getattr(odt, "tecnico_id", None),
                (checklist.check_metadata or {}).get("tecnico"),
            ),
            "supervisor": _pick_first(
                supervisor_nombre,
                (checklist.check_metadata or {}).get("supervisor"),
                getattr(odt, "supervisor_id", None),
            ),
            "proyecto": _pick_first(
                (checklist.check_metadata or {}).get("proyecto"),
            ),
            "unidad": _pick_first(
                _resolve_attr_chain(odt, "unidad.codigo"),
                _resolve_attr_chain(odt, "unidad.nombre"),
                getattr(odt, "unidad_id", None),
                (checklist.check_metadata or {}).get("unidad"),
            ),
            "cliente": cliente_nombre,
            "compania": _pick_first(_resolve_attr_chain(odt, "compania.nombre")),
            "prioridad": _pick_first(_resolve_attr_chain(odt, "prioridad.nombre")),
            "estado": _pick_first(_resolve_attr_chain(odt, "estado.nombre")),
        }
        branding = {
            "logo_url": "app/templates/logo.png",
            "logo_w": 100,
            "logo_h": 90,
            "logo2_url": "app/templates/logo2.png",  
            "logo2_w": 180,
            "logo2_h": 70,
        }

        # Ajustar timestamps al huso horario de Panamá y solo hora:minutos
        for it in items_enriquecidos:
            ts = it["seguimiento"]["timestamp"] if it.get("seguimiento") else None
            if ts:
                # Convertir a tz Panamá y formatear HH:MM
                ts_panama = ts.astimezone(LOCAL_TZ)
                it["hora_local"] = ts_panama.strftime("%H:%M")
            else:
                it["hora_local"] = None

        # Selección de plantilla según tipo_orden_id
        template_name = "reporte_checklist.html"
        if getattr(odt, "tipo_orden_id", None) == 67:
            template_name = "reporte_seguridad.html"
        if getattr(odt, "tipo_orden_id", None) == 101:
            template_name = "reporte_seguridadV2.html"

        # Tomar el primer timestamp válido como referencia de la inspección
        primer_ts = next((it["seguimiento"]["timestamp"] for it in items_enriquecidos if it.get("seguimiento") and it["seguimiento"].get("timestamp")), None)

        if primer_ts:
            ts_panama = primer_ts.astimezone(LOCAL_TZ)
            cabecera["fecha_ejecucion"] = ts_panama.strftime("%d/%m/%Y")
            cabecera["hora_ejecucion"] = ts_panama.strftime("%H:%M")
        else:
            cabecera["fecha_ejecucion"] = "-"
            cabecera["hora_ejecucion"] = "-"

        env = Environment(loader=FileSystemLoader("app/templates"))
        template = env.get_template(template_name)
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