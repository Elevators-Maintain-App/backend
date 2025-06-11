# app/services/ordenes.py
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.db.models.enums.estados_orden import EstadoOrden
from app.db.models.seguimiento import OrdenTrabajoSeguimiento, EventoOrden
from app.schemas.seguimiento import SeguimientoCreate


class OrdenService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ---------- helpers ---------- #
    async def _add_tracking(
        self,
        orden: OrdenDeTrabajo,
        datos: SeguimientoCreate,
        checklist_item_id: UUID | None = None,
    ) -> None:
        self.db.add(
            OrdenTrabajoSeguimiento(
                orden_id=orden.id,
                evento=datos.evento,
                lat=datos.lat,
                lon=datos.lon,
                timestamp=datos.timestamp or datetime.now(tz=timezone.utc),
                checklist_item_id=checklist_item_id,
            )
        )

    # ---------- casos de uso ---------- #
    async def iniciar(self, orden: OrdenDeTrabajo, datos: SeguimientoCreate) -> None:
        if orden.estado != EstadoOrden.PENDIENTE:
            raise HTTPException(status.HTTP_409_CONFLICT, "La orden ya fue iniciada")
        orden.estado = EstadoOrden.EN_EJECUCION
        await self._add_tracking(orden, datos)
        if orden.checklist:
            orden.checklist.inicio_lat = datos.lat
            orden.checklist.inicio_lon = datos.lon
            orden.checklist.inicio_hora = datos.timestamp or datetime.utcnow()

    async def pausar(self, orden: OrdenDeTrabajo, datos: SeguimientoCreate) -> None:
        if orden.estado != EstadoOrden.EN_EJECUCION:
            raise HTTPException(status.HTTP_409_CONFLICT, "La orden no está en ejecución")
        orden.estado = EstadoOrden.EN_PAUSA
        await self._add_tracking(orden, datos)

    async def reanudar(self, orden: OrdenDeTrabajo, datos: SeguimientoCreate) -> None:
        if orden.estado != EstadoOrden.EN_PAUSA:
            raise HTTPException(status.HTTP_409_CONFLICT, "La orden no está en pausa")
        orden.estado = EstadoOrden.EN_EJECUCION
        await self._add_tracking(orden, datos)

    async def finalizar(self, orden: OrdenDeTrabajo, datos: SeguimientoCreate) -> None:
        if orden.estado not in (EstadoOrden.EN_EJECUCION, EstadoOrden.EN_PAUSA):
            raise HTTPException(status.HTTP_409_CONFLICT, "La orden no está activa")
        orden.estado = EstadoOrden.FINALIZADA
        await self._add_tracking(orden, datos)
        if orden.checklist:
            orden.checklist.fin_hora = datos.timestamp or datetime.utcnow()

    async def paso_completado(
        self, orden: OrdenDeTrabajo, item_id: UUID, datos: SeguimientoCreate
    ) -> None:
        if orden.estado != EstadoOrden.EN_EJECUCION:
            raise HTTPException(status.HTTP_409_CONFLICT, "La orden no está en ejecución")
        await self._add_tracking(orden, datos, checklist_item_id=item_id)
