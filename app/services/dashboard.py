# app/services/dashboard.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.db.models.unidades import Unidad
from app.db.models.hojas_de_vida import HojaDeVida

class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_resumen_ordenes_trabajo(self):
        """
        Devuelve el conteo de órdenes por estado: abiertas, cerradas, pendientes.
        """
        result = await self.db.execute(
            select(
                OrdenDeTrabajo.estado_id,
                func.count(OrdenDeTrabajo.id)
            ).group_by(OrdenDeTrabajo.estado_id)
        )
        resumen = result.all()
        return {"resumen_ordenes": [{"estado_id": estado, "cantidad": cantidad} for estado, cantidad in resumen]}

    async def get_unidades_mantenimiento_pendiente(self):
        """
        Lista unidades con mantenimiento pendiente (ejemplo basado en criterio ficticio).
        """
        # Supongamos que si no existe hoja de vida o tiene registros viejos, requiere mantenimiento
        result = await self.db.execute(
            select(Unidad).outerjoin(HojaDeVida, Unidad.id == HojaDeVida.unidad_id).where(HojaDeVida.id.is_(None))
        )
        unidades = result.scalars().all()
        return unidades

    async def get_estadisticas_generales(self):
        """
        Devuelve estadísticas generales: órdenes por prioridad, estado y tipo de orden.
        """
        result_prioridades = await self.db.execute(
            select(
                OrdenDeTrabajo.prioridad_id,
                func.count(OrdenDeTrabajo.id)
            ).group_by(OrdenDeTrabajo.prioridad_id)
        )
        result_estados = await self.db.execute(
            select(
                OrdenDeTrabajo.estado_id,
                func.count(OrdenDeTrabajo.id)
            ).group_by(OrdenDeTrabajo.estado_id)
        )
        result_tipos_orden = await self.db.execute(
            select(
                OrdenDeTrabajo.tipo_orden_id,
                func.count(OrdenDeTrabajo.id)
            ).group_by(OrdenDeTrabajo.tipo_orden_id)
        )

        return {
            "ordenes_por_prioridad": [{"prioridad_id": prioridad, "cantidad": cantidad} for prioridad, cantidad in result_prioridades.all()],
            "ordenes_por_estado": [{"estado_id": estado, "cantidad": cantidad} for estado, cantidad in result_estados.all()],
            "ordenes_por_tipo_orden": [{"tipo_orden_id": tipo, "cantidad": cantidad} for tipo, cantidad in result_tipos_orden.all()],
        }
