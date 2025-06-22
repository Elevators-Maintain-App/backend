# app/api/routes/ordenes_seguimiento.py
from uuid import UUID

from fastapi import APIRouter, Body, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ordenes import OrdenService
from app.db.session import get_db
from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.schemas.seguimiento import SeguimientoCreate, EventoOrden
from app.auth.firebase import require_role  
from sqlalchemy import select
from sqlalchemy.orm import selectinload


router = APIRouter()


async def _get_orden(db: AsyncSession, orden_id: UUID) -> OrdenDeTrabajo:
    orden = await db.scalar(
    select(OrdenDeTrabajo)
      .options(selectinload(OrdenDeTrabajo.checklists))
      .where(OrdenDeTrabajo.id == orden_id)
    )
    if not orden:
        raise HTTPException(404, "Orden no encontrada")
    return orden


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


@router.post("/{orden_id}/finalizar", status_code=status.HTTP_204_NO_CONTENT)
async def finalizar_orden(
    orden_id: UUID,
    body: SeguimientoCreate = Body(...),
    user=Depends(require_role("technician")),
    db: AsyncSession = Depends(get_db),
):
    body.evento = EventoOrden.FIN
    orden = await _get_orden(db, orden_id)
    await OrdenService(db).finalizar(orden, body)
    await db.commit()


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

