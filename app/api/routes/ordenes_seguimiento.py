# app/api/routes/ordenes_seguimiento.py
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Body, Depends, status, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ordenes import OrdenService
from app.db.session import get_db
from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.db.models.checklists import Checklist, ChecklistItem
from app.schemas.seguimiento import SeguimientoCreate, EventoOrden, FinalizarOrdenPayload
from app.auth.firebase import require_role  
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.schemas.reportes import UrlReporteOut, ReportePrerevisionOut

from app.services.reportes.generar_pdf_service import generar_y_subir_pdf
from app.services.checklists import ChecklistService
from app.schemas.checklists_sync import ChecklistSyncPayload

import logging
logger = logging.getLogger("sync_checklist")

router = APIRouter()

# Helper function to get an order by ID
async def _get_orden(db: AsyncSession, orden_id: UUID) -> OrdenDeTrabajo:
    orden = await db.scalar(
    select(OrdenDeTrabajo)
      .options(selectinload(OrdenDeTrabajo.checklists))
      .where(OrdenDeTrabajo.id == orden_id)
    )
    if not orden:
        raise HTTPException(404, "Orden no encontrada")
    return orden

# Endpoint implementations

# Start an order
@router.post("/{orden_id}/iniciar", status_code=status.HTTP_204_NO_CONTENT)
async def iniciar_orden(
    orden_id: UUID,
    body: SeguimientoCreate = Body(...),
    user=Depends(require_role("technician")),
    db: AsyncSession = Depends(get_db),
):
    body.evento = EventoOrden.INICIO
    orden = await _get_orden(db, orden_id)
    await OrdenService(db).iniciar(orden, body)
    await db.commit()

# Pause an order
@router.post("/{orden_id}/pausar", status_code=status.HTTP_204_NO_CONTENT)
async def pausar_orden(
    orden_id: UUID,
    body: SeguimientoCreate = Body(...),
    user=Depends(require_role("technician")),
    db: AsyncSession = Depends(get_db),
):
    body.evento = EventoOrden.PAUSA
    orden = await _get_orden(db, orden_id)
    await OrdenService(db).pausar(orden, body)
    await db.commit()

# Resume an order
@router.post("/{orden_id}/reanudar", status_code=status.HTTP_204_NO_CONTENT)
async def reanudar_orden(
    orden_id: UUID,
    body: SeguimientoCreate = Body(...),
    user=Depends(require_role("technician")),
    db: AsyncSession = Depends(get_db),
):
    body.evento = EventoOrden.REANUDACION
    orden = await _get_orden(db, orden_id)
    await OrdenService(db).reanudar(orden, body)
    await db.commit()

# Send order for validation (generate prereport)
@router.post("/{orden_id}/validar", status_code=status.HTTP_204_NO_CONTENT)
async def enviar_orden_a_validacion(
    orden_id: UUID,
    background_tasks: BackgroundTasks,
    body: FinalizarOrdenPayload = Body(...),
    user=Depends(require_role("technician")),
    db: AsyncSession = Depends(get_db),
):
    body.evento = EventoOrden.PASO_COMPLETADO
    orden = await _get_orden(db, orden_id)
    await OrdenService(db).enviar_a_validacion(orden, body)
    await db.commit()
    # Generar PDF de prereporte en background
    background_tasks.add_task(generar_y_subir_pdf, orden_id, "prereporte")

# Finalize an order (generate final report)
@router.post("/{orden_id}/finalizar", status_code=status.HTTP_204_NO_CONTENT)
async def finalizar_orden(
    orden_id: UUID,
    background_tasks: BackgroundTasks,
    body: SeguimientoCreate = Body(...),
    user=Depends(require_role("supervisor")),  
    db: AsyncSession = Depends(get_db),
):
    body.evento = EventoOrden.FIN
    orden = await _get_orden(db, orden_id)
    await OrdenService(db).finalizar(orden, body)
    await db.commit()
    # Generar PDF de reporte final en background
    background_tasks.add_task(generar_y_subir_pdf, orden_id, "final")

# Complete a checklist item
@router.post("/{orden_id}/items/{item_id}/completar", status_code=status.HTTP_204_NO_CONTENT)
async def completar_item(
    orden_id: UUID,
    item_id: UUID,
    body: SeguimientoCreate = Body(...),
    user=Depends(require_role("technician")),
    db: AsyncSession = Depends(get_db),
):
    body.evento = EventoOrden.PASO_COMPLETADO
    orden = await _get_orden(db, orden_id)
    await OrdenService(db).paso_completado(orden, item_id, body)
    await db.commit()

# Complete a checklist step by step number
@router.post("/{orden_id}/pasos/{step_number}/completar", status_code=status.HTTP_204_NO_CONTENT)
async def completar_paso_por_orden(
    orden_id: UUID,
    step_number: int,
    body: SeguimientoCreate = Body(...),
    user=Depends(require_role("technician")),
    db: AsyncSession = Depends(get_db),
):
    body.evento = EventoOrden.PASO_COMPLETADO
    orden = await _get_orden(db, orden_id)

    # Obtener checklist asociado a la orden
    result = await db.execute(
        select(Checklist.id)
        .where(Checklist.orden_trabajo_id == orden_id)
    )
    checklist_id = result.scalar()
    if not checklist_id:
        raise HTTPException(status_code=404, detail="Checklist no encontrado")

    # Obtener item por checklist y step_number
    result = await db.execute(
        select(ChecklistItem.id)
        .where(ChecklistItem.checklist_id == checklist_id)
        .where(ChecklistItem.step_number == step_number)
    )
    item_id = result.scalar()
    if not item_id:
        raise HTTPException(status_code=404, detail="Paso no encontrado")

    await OrdenService(db).paso_completado(orden, item_id, body)
    await db.commit()

# Get URL for prereport
@router.get("/{orden_id}/reporte-prerevision", response_model=ReportePrerevisionOut)
async def obtener_url_reporte_prerevision(
    orden_id: UUID,
    user=Depends(require_role("supervisor")),  
    db: AsyncSession = Depends(get_db),
):
    orden_service = OrdenService(db)
    reporte_data = await orden_service.obtener_datos_reporte_prerevision(orden_id)
    
    if not reporte_data:
        raise HTTPException(status_code=404, detail="No se ha generado un prereporte para esta orden.")
    
    return reporte_data

# New Sync Checklist Endpoint for React Native App
@router.post("/{orden_id}/sync-validar", status_code=status.HTTP_204_NO_CONTENT)
async def sync_checklist_y_enviar_a_validacion(
    orden_id: UUID,
    background_tasks: BackgroundTasks,
    payload: ChecklistSyncPayload = Body(...),
    user=Depends(require_role("technician")),
    db: AsyncSession = Depends(get_db),
):
    if payload.orden_trabajo_id != orden_id:
        raise HTTPException(status_code=400, detail="orden_id no coincide con payload.orden_trabajo_id")

    orden = await _get_orden(db, orden_id)

    await ChecklistService(db).sync_full_checklist(orden_id, payload)

    # 2) Firmas: vienen en raíz o dentro del item de firmas
    firma_tecnico = payload.firma_tecnico
    firma_cliente = payload.firma_cliente

    if not (firma_tecnico and firma_cliente):
        # Compatibilidad con tu JSON RN (las firmas viven en evidencia_data del último paso)
        try:
            last_step = max([x.step_number for x in payload.items])
            firmas_item = next((x for x in payload.items if x.step_number == last_step), None)
            if firmas_item and isinstance(firmas_item.evidencia_data, dict):
                firma_tecnico = firma_tecnico or firmas_item.evidencia_data.get("Firma técnico")
                firma_cliente = firma_cliente or firmas_item.evidencia_data.get("Firma cliente")
        except Exception:
            pass

    ts = payload.hora_salida if isinstance(payload.hora_salida, datetime) else None

    finalizar = FinalizarOrdenPayload(
        evento=EventoOrden.PASO_COMPLETADO,
        lat=payload.lat,
        lon=payload.lon,
        timestamp=ts,
        firma_tecnico=firma_tecnico,
        firma_cliente=firma_cliente,
    )

    await OrdenService(db).enviar_a_validacion(orden, finalizar)
    await db.commit()

    # 3) PDF prereporte en background
    background_tasks.add_task(generar_y_subir_pdf, orden_id, "prereporte")