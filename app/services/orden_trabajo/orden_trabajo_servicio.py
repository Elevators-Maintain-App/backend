#app/services/orden_trabajo/orden_trabajo_servicio.py

from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract, case
from sqlalchemy.orm import selectinload
from app.schemas.dashboard.technician import DashboardTecnicoOut, OrdenEnCursoOut
from app.schemas.dashboard.supervisor import OrdenResumenSupervisor, DashboardSupervisorOut

from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.db.models.usuarios import Usuario
from app.db.models.unidades import Unidad
from app.db.repositories.ordenes_de_trabajo import orden_de_trabajo_crud
from app.schemas.ordenes_de_trabajo import (
    OrdenDeTrabajoCreate,
    OrdenTrabajoDetailOut,
    OrdenDeTrabajoSummaryOut,
    OrdenDeTrabajoUpdate
)
from app.services.orden_trabajo.user_cases import FabricaDeOrdenesTabajo
from app.core.exceptions import ForbiddenException
import logging

logger = logging.getLogger(__name__)

class OrdenTrabajoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, usuario_actual: Usuario, skip: Optional[int] = 0, limit: Optional[int] = None, search: Optional[str] = None, company_id: Optional[str] = None, estado_id: Optional[int] = None, tipo_orden_id: Optional[int] = None, prioridad_id: Optional[int] = None) -> List[OrdenDeTrabajoSummaryOut]:
        """
        Obtiene órdenes de trabajo con filtros basados en el rol del usuario
        """
        try:
            fabrica_de_ordenes = FabricaDeOrdenesTabajo.get_orden_trabajo_case(usuario_actual.rol)
            filtros = fabrica_de_ordenes.obtener_filtros_para_listar_ordenes(usuario_actual, search, company_id, estado_id, tipo_orden_id, prioridad_id)
            
            ordenes = await orden_de_trabajo_crud.get_multi_with_advanced_filters(
                self.db, 
                skip=skip, 
                limit=limit, 
                exact_filters=filtros.get("exact_filters", None), 
                ilike_filters=filtros.get("ilike_filters", None), 
                like_filters=filtros.get("like_filters", None)
            )
            
            return [OrdenDeTrabajoSummaryOut.from_orm(orden) for orden in ordenes]
        except Exception as e:
            logger.error(f"Error get_all ordenes: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener las órdenes de trabajo")
        
    async def get_total_ordenes(self, usuario_actual: Usuario, company_id: Optional[UUID] = None, estado_id: Optional[int] = None, tipo_orden_id: Optional[int] = None, prioridad_id: Optional[int] = None) -> int:
        """
        Obtiene el total de órdenes de trabajo basado en los permisos del usuario
        """
        try:
            fabrica_de_ordenes = FabricaDeOrdenesTabajo.get_orden_trabajo_case(usuario_actual.rol)
            filtro_para_totalizar_ordenes = fabrica_de_ordenes.obtener_filtro_para_totalizar_ordenes(usuario_actual, company_id, estado_id, tipo_orden_id, prioridad_id)
            
            cantidad_de_ordenes = await orden_de_trabajo_crud.get_total_with_advanced_filters(
                self.db, 
                exact_filters=filtro_para_totalizar_ordenes.get("exact_filters", None), 
                ilike_filters=filtro_para_totalizar_ordenes.get("ilike_filters", None), 
                like_filters=filtro_para_totalizar_ordenes.get("like_filters", None)
            )
            return cantidad_de_ordenes
        except Exception as e:
            logger.error(f"Error get_total_ordenes: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener la cantidad de órdenes de trabajo")

    async def get_by_id(self, orden_id: UUID, usuario_actual: Usuario) -> OrdenTrabajoDetailOut:
        """
        Obtiene una orden de trabajo por su ID basado en los permisos del usuario
        """
        fabrica_de_ordenes = FabricaDeOrdenesTabajo.get_orden_trabajo_case(usuario_actual.rol)
        
        orden = await orden_de_trabajo_crud.get(self.db, orden_id)
        if not orden:
            raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
        
        if not fabrica_de_ordenes.puede_ver_orden(usuario_actual, str(orden_id), orden.company_id, orden.supervisor_id, orden.tecnico_id):
            raise ForbiddenException("No tienes permisos para ver esta orden de trabajo")
        
        # Aquí se puede implementar la lógica para construir el OrdenTrabajoDetailOut
        # similar a la implementación existente en get_detail
        return await self._build_detail_response(orden)

    async def create(self, orden_in: OrdenDeTrabajoCreate, usuario_actual: Usuario) -> OrdenDeTrabajoSummaryOut:
        """
        Crea una nueva orden de trabajo basado en los permisos del usuario
        """
        fabrica_de_ordenes = FabricaDeOrdenesTabajo.get_orden_trabajo_case(usuario_actual.rol)
        
        if not fabrica_de_ordenes.puede_crear_ordenes(usuario_actual):
            raise ForbiddenException("No tienes permisos para crear órdenes de trabajo")
        
        # Para Admin y Supervisor, la orden debe pertenecer a su compañía
        if usuario_actual.rol in ['admin', 'supervisor']:
            orden_in.company_id = usuario_actual.company_id
        
        # Si es supervisor, se auto-asigna como supervisor
        if usuario_actual.rol == 'supervisor':
            orden_in.supervisor_id = str(usuario_actual.id)
        
        orden_guardada = await orden_de_trabajo_crud.create(self.db, obj_in=orden_in)
        return OrdenDeTrabajoSummaryOut.from_orm(orden_guardada)

    async def update(self, orden_id: UUID, orden_in: OrdenDeTrabajoUpdate, usuario_actual: Usuario) -> OrdenDeTrabajoSummaryOut:
        """
        Actualiza una orden de trabajo basado en los permisos del usuario
        """
        fabrica_de_ordenes = FabricaDeOrdenesTabajo.get_orden_trabajo_case(usuario_actual.rol)
        
        if not fabrica_de_ordenes.puede_gestionar_ordenes(usuario_actual):
            raise ForbiddenException("No tienes permisos para actualizar órdenes de trabajo")
        
        orden_db = await orden_de_trabajo_crud.get(self.db, orden_id)
        if not orden_db:
            raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
        
        if not fabrica_de_ordenes.puede_ver_orden(usuario_actual, str(orden_id), orden_db.company_id, orden_db.supervisor_id, orden_db.tecnico_id):
            raise ForbiddenException("No tienes permisos para actualizar esta orden de trabajo")

        orden_actualizada = await orden_de_trabajo_crud.update(self.db, db_obj=orden_db, obj_in=orden_in)
        return OrdenDeTrabajoSummaryOut.from_orm(orden_actualizada)

    async def delete(self, orden_id: UUID, usuario_actual: Usuario) -> None:
        """
        Elimina una orden de trabajo basado en los permisos del usuario
        """
        fabrica_de_ordenes = FabricaDeOrdenesTabajo.get_orden_trabajo_case(usuario_actual.rol)
        
        if not fabrica_de_ordenes.puede_eliminar_ordenes(usuario_actual):
            raise ForbiddenException("No tienes permisos para eliminar órdenes de trabajo")
        
        orden_db = await orden_de_trabajo_crud.get(self.db, orden_id)
        if not orden_db:
            raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
        
        if not fabrica_de_ordenes.puede_ver_orden(usuario_actual, str(orden_id), orden_db.company_id, orden_db.supervisor_id, orden_db.tecnico_id):
            raise ForbiddenException("No tienes permisos para eliminar esta orden de trabajo")

        await orden_de_trabajo_crud.remove(self.db, orden_id)

    # Métodos de conteo específicos por rol (manteniendo compatibilidad)
    async def count_by_company(self, company_id: UUID, usuario_actual: Usuario) -> int:
        """Conteo de órdenes por compañía (solo Admin/SuperAdmin)"""
        fabrica_de_ordenes = FabricaDeOrdenesTabajo.get_orden_trabajo_case(usuario_actual.rol)
        if not fabrica_de_ordenes.puede_gestionar_ordenes(usuario_actual):
            raise ForbiddenException("No tienes permisos para ver estadísticas de la compañía")
        
        return await self.get_total_ordenes(usuario_actual, company_id=company_id)

    async def count_by_supervisor(self, supervisor_uid: str, usuario_actual: Usuario) -> int:
        """Conteo de órdenes por supervisor"""
        if usuario_actual.rol == 'supervisor' and str(usuario_actual.id) != supervisor_uid:
            raise ForbiddenException("Solo puedes ver tus propias estadísticas")
        
        return await self.get_total_ordenes(usuario_actual)

    async def count_by_technician(self, technician_uid: str, usuario_actual: Usuario) -> int:
        """Conteo de órdenes por técnico"""
        if usuario_actual.rol == 'technician' and str(usuario_actual.id) != technician_uid:
            raise ForbiddenException("Solo puedes ver tus propias estadísticas")
        
        return await self.get_total_ordenes(usuario_actual)

    async def _build_detail_response(self, orden: OrdenDeTrabajo) -> OrdenTrabajoDetailOut:
        """
        Construye la respuesta detallada de una orden de trabajo
        Este método encapsula la lógica compleja de construcción del detalle
        """
        # Aquí se implementaría la lógica existente de get_detail
        # Por ahora, devolvemos una versión simplificada
        return OrdenTrabajoDetailOut(
            referencia=orden.referencia,
            descripcion=orden.descripcion,
            tipo_orden="",  # Se obtendría de la relación
            proyecto="",    # Se obtendría de la relación
            prioridad="",   # Se obtendría de la relación
            supervisor="",  # Se obtendría de Firebase
            unidad="",      # Se obtendría de la relación
            cliente="",     # Se obtendría de la relación
            estado="",      # Se obtendría de la relación
            observaciones=orden.observaciones or ""
        ) 
    
    # Dashboard Técnico
    async def get_dashboard_data(self, technician_uid: str, company_id, fecha_inicio: date, fecha_fin: date) -> DashboardTecnicoOut:
        # Estados por categoría
        estados_completadas = [4, 5]  # En validación, Cerrada
        estados_pendientes = [1, 3, 6]  # Pendiente, En ejecución, En pausa

        # Query base
        filtro_base = and_(
            OrdenDeTrabajo.tecnico_id == str(technician_uid),
            OrdenDeTrabajo.company_id == str(company_id),
            OrdenDeTrabajo.fecha >= fecha_inicio,
            OrdenDeTrabajo.fecha <= fecha_fin,
        )
        
        # 1. Métricas del período en una sola consulta, manteniendo filtros y categorías actuales.
        metricas_stmt = select(
            func.count().label("total"),
            func.coalesce(
                func.sum(case((OrdenDeTrabajo.estado_id.in_(estados_completadas), 1), else_=0)),
                0,
            ).label("completadas"),
            func.coalesce(
                func.sum(case((OrdenDeTrabajo.estado_id.in_(estados_pendientes), 1), else_=0)),
                0,
            ).label("pendientes"),
        ).where(filtro_base)
        metricas = (await self.db.execute(metricas_stmt)).one()
        total = metricas.total
        completadas = metricas.completadas
        pendientes = metricas.pendientes

        # 2. Lista de órdenes en curso
        ordenes_stmt = (
            select(OrdenDeTrabajo)
            .where(filtro_base)
            .options(
                selectinload(OrdenDeTrabajo.unidad).selectinload(Unidad.proyecto),
                selectinload(OrdenDeTrabajo.estado),
                selectinload(OrdenDeTrabajo.tipo_orden),
                selectinload(OrdenDeTrabajo.prioridad),
                selectinload(OrdenDeTrabajo.cliente),
                selectinload(OrdenDeTrabajo.tecnico),
            )
            .order_by(OrdenDeTrabajo.fecha.asc())
        )
        res = await self.db.execute(ordenes_stmt)

        # Asignar prioridad de ordenamiento por estado
        estado_prioridad = {
            "En ejecución": 1,
            "En Pausa": 2,
            "Pendiente": 3,
            "En Validación": 4,
            "Cerrada": 5,
        }

        ordenes = []
        for o in res.scalars().all():
            ordenes.append((
                estado_prioridad.get(o.estado.nombre, 99),  # valor por defecto alto si no está en el dict
                OrdenEnCursoOut(
                    id=o.id,
                    cliente=o.cliente.nombre if o.cliente else None,
                    proyecto=o.unidad.proyecto.nombre,
                    unidad=o.unidad.nombre,
                    descripcion=o.descripcion,
                    observaciones=o.observaciones or "",
                    estado=o.estado.nombre,
                    fecha_programada=o.fecha,
                    prioridad=o.prioridad.nombre,
                    tipo_orden=o.tipo_orden.nombre,
                    tecnico=o.tecnico.display_name if o.tecnico else None
                )
            ))

        # Ordenar por prioridad
        ordenes.sort(key=lambda x: x[0])
        ordenes_final = [o[1] for o in ordenes]

        cumplimiento = completadas / total if total else 0.0

        return DashboardTecnicoOut(
            ordenes_programadas=total,
            ordenes_completadas=completadas,
            ordenes_pendientes=pendientes,
            cumplimiento_decimal=round(cumplimiento, 4),
            cumplimiento_str = f"{int(cumplimiento * 100)}%",
            cumplimiento_label=f"{completadas} órdenes completadas de {total} órdenes totales",
            ordenes_en_curso=ordenes_final
        )
    
    # Dashboard Supervisor
    async def get_dashboard_data_supervisor(
        self,
        supervisor_uid: str,
        company_id: UUID,
        fecha_inicio: date,
        fecha_fin: date
    ) -> DashboardSupervisorOut:
        estados_cerradas = [4]
        estados_por_validar = [1]
        estados_pendientes = [3]
        estados_ejecucion = [2]
        estados_atrasadas = [5]

        filtro_base = and_(
            OrdenDeTrabajo.supervisor_id == supervisor_uid,
            OrdenDeTrabajo.company_id == company_id,
            OrdenDeTrabajo.fecha >= fecha_inicio,
            OrdenDeTrabajo.fecha <= fecha_fin
        )

        # Query con relaciones
        ordenes_stmt = (
            select(OrdenDeTrabajo)
            .where(filtro_base)
            .options(
                selectinload(OrdenDeTrabajo.unidad).selectinload(Unidad.proyecto),
                selectinload(OrdenDeTrabajo.estado),
                selectinload(OrdenDeTrabajo.tipo_orden),
                selectinload(OrdenDeTrabajo.prioridad),
                selectinload(OrdenDeTrabajo.cliente),
                selectinload(OrdenDeTrabajo.tecnico)
            )
            .order_by(OrdenDeTrabajo.fecha.asc())
        )
        res = await self.db.execute(ordenes_stmt)

        estado_prioridad = {
            "En ejecución": 1,
            "En Pausa": 2,
            "Pendiente": 3,
            "En Validación": 4,
            "Cerrada": 5
        }

        ordenes_raw = res.scalars().all()
        total = len(ordenes_raw)
        cerradas = por_validar = pendientes = en_ejecucion = atrasadas = 0
        ordenes: List[tuple[int, OrdenResumenSupervisor]] = []

        for o in ordenes_raw:
            estado = o.estado.nombre if o.estado else "—"

            match o.estado_id:
                case 5: cerradas += 1          # Cerrada
                case 4: por_validar += 1       # En Validación
                case 1: pendientes += 1        # Pendiente
                case 3: en_ejecucion += 1      # En ejecución
                case 6: atrasadas += 1         # En Pausa

            ordenes.append((
                estado_prioridad.get(estado, 99),
                OrdenResumenSupervisor(
                    id=o.id,
                    cliente=o.cliente.nombre if o.cliente else "—",
                    tecnico=o.tecnico.display_name if o.tecnico else "—",
                    proyecto=o.unidad.proyecto.nombre if o.unidad and o.unidad.proyecto else "—",
                    unidad=o.unidad.nombre if o.unidad else "—",
                    descripcion=o.descripcion,
                    observaciones=o.observaciones or "",
                    estado=estado,
                    fecha_programada=o.fecha,
                    prioridad=o.prioridad.nombre if o.prioridad else "—",
                    tipo_orden=o.tipo_orden.nombre if o.tipo_orden else "—"
                )
            ))

        ordenes.sort(key=lambda x: x[0])
        resumen_final = [o[1] for o in ordenes]

        cumplimiento = cerradas
        cumplimiento_pct = cumplimiento / total if total else 0.0

        return DashboardSupervisorOut(
            ordenes_programadas=total,
            ordenes_cerradas=cerradas,
            ordenes_por_validar=por_validar,
            ordenes_pendientes=pendientes,
            ordenes_en_ejecucion=en_ejecucion,
            ordenes_atrasadas=atrasadas,
            cumplimiento_decimal=round(cumplimiento_pct, 4),
            cumplimiento_label=f"{cumplimiento} órdenes cerradas de {total} órdenes totales",
            cumplimiento_str=f"{int(cumplimiento_pct * 100)}%",
            ordenes=resumen_final
        )
