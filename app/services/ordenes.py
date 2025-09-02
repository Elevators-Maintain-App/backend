# app/services/ordenes.py
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.db.models.seguimiento import OrdenTrabajoSeguimiento, EventoOrden
from app.schemas.seguimiento import SeguimientoCreate, FinalizarOrdenPayload
from app.utils.estados_orden import EstadoOrdenID
from app.db.models.proyectos import Proyecto
from app.db.models.unidades import Unidad
from app.db.models.checklists import Checklist
from app.schemas.reportes import UrlReporteOut, ReportePrerevisionOut
from sqlalchemy import select

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
        orden.estado_id = EstadoOrdenID.EN_EJECUCION
        await self._add_tracking(orden, datos)
        for checklist in orden.checklists:
            if checklist.hora_entrada is None:
                checklist.hora_entrada = (datos.timestamp or datetime.utcnow()).time()

    async def pausar(self, orden: OrdenDeTrabajo, datos: SeguimientoCreate) -> None:
        orden.estado_id = EstadoOrdenID.EN_PAUSA
        await self._add_tracking(orden, datos)

    async def reanudar(self, orden: OrdenDeTrabajo, datos: SeguimientoCreate) -> None:
        
        orden.estado_id = EstadoOrdenID.EN_EJECUCION
        await self._add_tracking(orden, datos)

    async def enviar_a_validacion(self, orden: OrdenDeTrabajo, datos: FinalizarOrdenPayload) -> None:
        orden.estado_id = EstadoOrdenID.EN_VALIDACION
        await self._add_tracking(orden, datos)
        for checklist in orden.checklists:
            if checklist.hora_salida is None:
                checklist.hora_salida = (datos.timestamp or datetime.utcnow()).time()
            if datos.firma_tecnico:
                checklist.firma_tecnico = datos.firma_tecnico
            if datos.firma_cliente:
                checklist.firma_cliente = datos.firma_cliente

    async def finalizar(self, orden: OrdenDeTrabajo, datos: SeguimientoCreate) -> None:
        orden.estado_id = EstadoOrdenID.COMPLETADA
        await self._add_tracking(orden, datos)

    async def paso_completado(
        self, orden: OrdenDeTrabajo, item_id: UUID, datos: SeguimientoCreate
    ) -> None:
        
        await self._add_tracking(orden, datos, checklist_item_id=item_id)

    async def obtener_datos_reporte_prerevision(self, orden_id: UUID) -> ReportePrerevisionOut | None:
        """Obtiene los datos completos del reporte de prerevision para una orden"""
        result = await self.db.execute(
            select(
                Checklist.reporte_prerevision_url,
                Proyecto.nombre.label('proyecto_nombre'),
                Unidad.nombre.label('unidad_nombre'),
                OrdenDeTrabajo.estado_id,
                OrdenDeTrabajo.fecha
            )
            .join(OrdenDeTrabajo, Checklist.orden_trabajo_id == OrdenDeTrabajo.id)
            .join(Unidad, OrdenDeTrabajo.unidad_id == Unidad.id)
            .join(Proyecto, Unidad.proyecto_id == Proyecto.id)
            .where(Checklist.orden_trabajo_id == orden_id)
        )
        
        row = result.first()
        if not row or not row.reporte_prerevision_url:
            return None
        
        estado_nombre = self._get_estado_nombre(row.estado_id)
        
        return ReportePrerevisionOut(
            url=row.reporte_prerevision_url,
            proyecto=row.proyecto_nombre,
            unidad=row.unidad_nombre,
            estado=estado_nombre,
            fecha=row.fecha
        )
    
    def _get_estado_nombre(self, estado_id: int) -> str:
        """Convierte el ID del estado a nombre legible"""
        # Ajusta según tu mapeo de estados
        estados = {
            EstadoOrdenID.PENDIENTE: "Pendiente",
            EstadoOrdenID.EN_EJECUCION: "En Ejecución", 
            EstadoOrdenID.EN_PAUSA: "En Pausa",
            EstadoOrdenID.EN_VALIDACION: "En Validación",
            EstadoOrdenID.COMPLETADA: "Completada"
        }
        return estados.get(estado_id, "Estado desconocido")