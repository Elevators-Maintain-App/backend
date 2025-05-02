# app/services/supervisores.py

from typing import List
from uuid import UUID
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.repositories.supervisores import supervisor_crud
from app.db.repositories.ordenes_de_trabajo import orden_de_trabajo_crud
from app.db.repositories.tecnicos import tecnico_crud
from app.db.repositories.unidades import unidad_crud
from app.db.repositories.proyectos import proyecto_crud
from app.db.repositories.estados_orden import estado_orden_crud
from app.schemas.supervisores import SupervisorCreate, SupervisorUpdate, SupervisorInDBBase, DashboardSupervisorOut, OrdenDashboardOut
from app.schemas.ordenes_de_trabajo import OrdenDeTrabajoInDBBase

class SupervisorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[SupervisorInDBBase]:
        return await supervisor_crud.get_multi(self.db)

    async def get_by_id(self, supervisor_id: UUID) -> SupervisorInDBBase:
        supervisor = await supervisor_crud.get(self.db, supervisor_id)
        if not supervisor:
            raise HTTPException(status_code=404, detail="Supervisor no encontrado")
        return supervisor

    async def create(self, supervisor_in: SupervisorCreate) -> SupervisorInDBBase:
        existing_nombre = await supervisor_crud.get_by_field(self.db, field="nombre", value=supervisor_in.nombre)
        if existing_nombre:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un supervisor con este nombre."
            )
        return await supervisor_crud.create(self.db, obj_in=supervisor_in)

    async def update(self, supervisor_id: UUID, supervisor_in: SupervisorUpdate) -> SupervisorInDBBase:
        supervisor_db = await supervisor_crud.get(self.db, supervisor_id)
        if not supervisor_db:
            raise HTTPException(status_code=404, detail="Supervisor no encontrado")
        return await supervisor_crud.update(self.db, db_obj=supervisor_db, obj_in=supervisor_in)

    async def delete(self, supervisor_id: UUID) -> None:
        supervisor_db = await supervisor_crud.get(self.db, supervisor_id)
        if not supervisor_db:
            raise HTTPException(status_code=404, detail="Supervisor no encontrado")
        await supervisor_crud.remove(self.db, supervisor_id)

    async def get_ordenes_trabajo(self, supervisor_id: UUID, skip: int = 0, limit: int = 10) -> List[OrdenDeTrabajoInDBBase]:
        ordenes = await orden_de_trabajo_crud.get_multi_by_field(self.db, field="supervisor_id", value=supervisor_id, skip=skip, limit=limit)
        return ordenes

    async def get_dashboard(self, supervisor_id: UUID) -> DashboardSupervisorOut:
        from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo

        # Obtener KPIs
        total_mes_stmt = select(func.count()).where(
            OrdenDeTrabajo.supervisor_id == supervisor_id,
            func.date_part('month', OrdenDeTrabajo.created_at) == func.date_part('month', func.now()),
            func.date_part('year', OrdenDeTrabajo.created_at) == func.date_part('year', func.now())
        )
        pendientes_stmt = total_mes_stmt.where(OrdenDeTrabajo.estado_id == 1)  # ID de estado pendiente
        finalizadas_stmt = total_mes_stmt.where(OrdenDeTrabajo.estado_id == 5)  # ID de estado finalizada
        en_progreso_stmt = total_mes_stmt.where(OrdenDeTrabajo.estado_id == 3)  # ID de estado en progreso

        total_mes = (await self.db.execute(total_mes_stmt)).scalar()
        pendientes = (await self.db.execute(pendientes_stmt)).scalar()
        finalizadas = (await self.db.execute(finalizadas_stmt)).scalar()
        en_progreso = (await self.db.execute(en_progreso_stmt)).scalar()
        porcentaje_finalizadas = round(float(finalizadas) / total_mes, 2) if total_mes > 0 else 0.0
        finalizadas_info = f"{finalizadas}/{total_mes}"

        # Obtener últimas 10 órdenes recientes no finalizadas
        ordenes_recientes_stmt = select(OrdenDeTrabajo).where(
            OrdenDeTrabajo.supervisor_id == supervisor_id,
            OrdenDeTrabajo.estado_id != 3
        ).order_by(OrdenDeTrabajo.created_at.desc()).limit(10)

        ordenes_recientes_result = (await self.db.execute(ordenes_recientes_stmt)).scalars().all()

        ordenes_recientes = []
        for orden in ordenes_recientes_result:
            tecnico = await tecnico_crud.get(self.db, orden.tecnico_id) if orden.tecnico_id else None
            unidad = await unidad_crud.get(self.db, orden.unidad_id) if orden.unidad_id else None
            proyecto = await proyecto_crud.get(self.db, unidad.proyecto_id) if unidad and unidad.proyecto_id else None
            estado = await estado_orden_crud.get(self.db, orden.estado_id) if orden.estado_id else None

            ordenes_recientes.append(OrdenDashboardOut(
                id_orden=orden.id,
                proyecto_nombre=proyecto.nombre if proyecto else None,
                tecnico_nombre=tecnico.nombre if tecnico else None,
                tecnico_nivel=tecnico.nivel if tecnico else None,
                fecha_creacion=orden.created_at,
                estado_orden=estado.nombre if estado else None,
                descripcion=orden.descripcion,
                observaciones=orden.observaciones,
                valor=orden.valor
            ))

        return DashboardSupervisorOut(
            ordenes_totales_mes=total_mes or 0,
            ordenes_pendientes=pendientes or 0,
            ordenes_finalizadas=finalizadas or 0,
            ordenes_en_progreso=en_progreso or 0,
            ordenes_recientes=ordenes_recientes,
            porcentaje_ordenes_finalizadas_mes=porcentaje_finalizadas,
            ordenes_finalizadas_info=finalizadas_info
        )