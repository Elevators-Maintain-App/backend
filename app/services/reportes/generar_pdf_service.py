# app/services/reportes/generar_pdf_service.py

from __future__ import annotations

import io
from datetime import timezone
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from weasyprint import HTML

from app.db.models.checklists import Checklist
from app.db.models.clientes import Cliente
from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.db.models.seguimiento import EventoOrden, OrdenTrabajoSeguimiento
from app.db.models.unidades import Unidad
from app.db.models.usuarios import Usuario
from app.db.session import AsyncSessionLocal
from app.services.firebase_storage.firebase_storage import subir_pdf_a_storage

LOCAL_TZ = ZoneInfo("America/Panama")


async def _geo_por_item(db: AsyncSession, checklist_item_ids):
    """Retorna {item_id: {"lat": float, "lon": float, "timestamp": datetime_tzaware}} para el seguimiento más reciente."""
    if not checklist_item_ids:
        return {}

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
    for seg in rows:
        iid = seg.checklist_item_id
        if iid in geo:
            continue
        if seg.lat is None or seg.lon is None:
            continue

        ts = seg.timestamp
        if ts and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        geo[iid] = {"lat": seg.lat, "lon": seg.lon, "timestamp": ts}

    return geo


def _resolve_attr_chain(obj, chain: str):
    cur = obj
    for part in chain.split("."):
        if cur is None:
            return None
        cur = getattr(cur, part, None)
    return cur


def _extract_evidence_urls(evidencia_data: dict) -> list[str]:
    """Convierte evidencia_data (cualquier formato) en lista de URLs para render."""
    if not evidencia_data:
        return []

    urls: list[str] = []

    if isinstance(evidencia_data.get("url"), str):
        urls.append(evidencia_data["url"])

    for k in ("url1", "url2", "url3"):
        v = evidencia_data.get(k)
        if isinstance(v, str) and v:
            urls.append(v)

    if isinstance(evidencia_data.get("urls"), list):
        for u in evidencia_data["urls"]:
            if isinstance(u, str) and u:
                urls.append(u)

    if isinstance(evidencia_data.get("photo"), str) and evidencia_data["photo"]:
        urls.append(evidencia_data["photo"])

    for k, v in evidencia_data.items():
        if isinstance(v, str) and v and k not in {"url", "url1", "url2", "url3", "photo"}:
            if v not in urls:
                urls.append(v)

    return urls


def _pick_first(*vals):
    for v in vals:
        if v:
            return v
    return None


def _format_hora_panama(ts):
    if not ts:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(LOCAL_TZ).strftime("%H:%M")


def _build_maps_link_from_checklist(checklist: Checklist) -> str | None:
    """
    Genera un link a Google Maps a partir del GPS almacenado en metadata.
    - Prioridad: check_metadata["gps"] (lo que guarda sync_full_checklist)
    - Fallback: check_metadata["gps_inicio"] (lo que guarda el RN en bootstrap)
    """
    md = checklist.check_metadata or {}

    lat = None
    lon = None

    gps = md.get("gps")
    if isinstance(gps, dict):
        lat = gps.get("lat")
        lon = gps.get("lon")

    if lat is None or lon is None:
        gps_inicio = md.get("gps_inicio")
        if isinstance(gps_inicio, dict):
            lat = gps_inicio.get("lat")
            lon = gps_inicio.get("lon")

    try:
        if lat is None or lon is None:
            return None
        lat_f = float(lat)
        lon_f = float(lon)
        if lat_f == 0 and lon_f == 0:
            return None
        return f"https://www.google.com/maps/search/?api=1&query={lat_f},{lon_f}"
    except Exception:
        return None


async def generar_y_subir_pdf(orden_id, tipo: str = "prereporte") -> str:
    """Genera el PDF (prereporte o final), lo sube a storage y guarda la URL en Checklist."""
    async with AsyncSessionLocal() as db:
        checklist = await db.scalar(
            select(Checklist)
            .options(
                selectinload(Checklist.items),
                selectinload(Checklist.orden_de_trabajo).selectinload(OrdenDeTrabajo.unidad),
                selectinload(Checklist.orden_de_trabajo).selectinload(OrdenDeTrabajo.compania),
                selectinload(Checklist.orden_de_trabajo).selectinload(OrdenDeTrabajo.tipo_orden),
                selectinload(Checklist.orden_de_trabajo).selectinload(OrdenDeTrabajo.estado),
                selectinload(Checklist.orden_de_trabajo).selectinload(OrdenDeTrabajo.prioridad),
                selectinload(Checklist.orden_de_trabajo)
                .selectinload(OrdenDeTrabajo.unidad)
                .selectinload(Unidad.proyecto),
            )
            .where(Checklist.orden_trabajo_id == orden_id)
        )
        if not checklist:
            raise ValueError("Checklist no encontrado")

        odt = getattr(checklist, "orden_de_trabajo", None)

        supervisor_nombre = None
        if odt and getattr(odt, "supervisor_id", None):
            sup = await db.scalar(select(Usuario).where(Usuario.uid == odt.supervisor_id))
            if sup:
                supervisor_nombre = (
                    getattr(sup, "nombre", None) or getattr(sup, "display_name", None) or odt.supervisor_id
                )

        cliente_nombre = None
        if odt and getattr(odt, "cliente_id", None):
            cli = await db.scalar(select(Cliente).where(Cliente.id == odt.cliente_id))
            if cli:
                cliente_nombre = (
                    getattr(cli, "nombre", None) or getattr(cli, "display_name", None) or odt.cliente_id
                )

        item_ids = [it.id for it in (checklist.items or [])]
        geo = await _geo_por_item(db, item_ids)

        items_enriquecidos = []
        for it in sorted(checklist.items or [], key=lambda x: x.step_number):
            meta = geo.get(it.id)
            evidencia_data = it.evidencia_data or {}
            items_enriquecidos.append(
                {
                    "id": it.id,
                    "step_number": it.step_number,
                    "titulo": it.titulo,
                    "instrucciones": it.instrucciones,
                    "comentario": it.comentario,
                    "evidencia_schema": it.evidencia_schema or {},
                    "evidencia_data": evidencia_data,
                    "evidencia_urls": _extract_evidence_urls(evidencia_data),
                    "seguimiento": meta,
                    "hora_local": _format_hora_panama(meta.get("timestamp")) if meta else None,
                }
            )

        template_name = "reporte_checklist.html"
        if getattr(odt, "tipo_orden_id", None) == 67:
            template_name = "reporte_seguridad.html"
        if getattr(odt, "tipo_orden_id", None) == 101:
            template_name = "reporte_seguridadV2.html"

        primer_ts = next(
            (
                it["seguimiento"]["timestamp"]
                for it in items_enriquecidos
                if it.get("seguimiento") and it["seguimiento"].get("timestamp")
            ),
            None,
        )

        if primer_ts:
            if primer_ts.tzinfo is None:
                primer_ts = primer_ts.replace(tzinfo=timezone.utc)
            ts_panama = primer_ts.astimezone(LOCAL_TZ)
            fecha_ejecucion = ts_panama.strftime("%d/%m/%Y")
            hora_ejecucion = ts_panama.strftime("%H:%M")
        else:
            odt_fecha = getattr(odt, "fecha", None)
            fecha_ejecucion = odt_fecha.strftime("%d/%m/%Y") if odt_fecha else "-"
            hs = checklist.hora_entrada or checklist.hora_salida
            hora_ejecucion = hs.strftime("%H:%M") if hs else "-"

        cabecera = {
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
                _resolve_attr_chain(odt, "proyecto.nombre"),
                _resolve_attr_chain(odt, "proyecto.nombre_proyecto"),
                _resolve_attr_chain(odt, "proyecto"),
                _resolve_attr_chain(odt, "unidad.proyecto.nombre"),
                _resolve_attr_chain(odt, "unidad.proyecto.nombre_proyecto"),
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
            "fecha_ejecucion": fecha_ejecucion,
            "hora_ejecucion": hora_ejecucion,
            "maps_link": _build_maps_link_from_checklist(checklist),
        }

        branding = {
            "logo_url": "app/templates/logo.png",
            "logo_w": 100,
            "logo_h": 90,
            "logo2_url": "app/templates/logo2.png",
            "logo2_w": 180,
            "logo2_h": 70,
        }

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
