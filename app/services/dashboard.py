# app/services/dashboard.py

from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.db.models.unidades import Unidad
from app.db.models.hojas_de_vida import HojaDeVida
from app.db.models.usuarios import Usuario
from app.db.models.compania import Compania
from app.db.models.proyectos import Proyecto
from app.db.models.clientes import Cliente
from app.auth.firebase import FirebaseUser
from app.constantes.ordenes_status import EstadoOrden
from app.schemas.proyectos import ProyectoEstado
from app.schemas.dashboard.supervisor import SupervisorDashboard
from app.schemas.dashboard.technician import TechnicianDashboard
from app.schemas.dashboard.cliente import ClienteDashboard, ClienteDashboardProyecto
from app.services.proyectos import ProyectoService
from app.services.unidades import UnidadService
from app.services.ordenes_de_trabajo import OrdenDeTrabajoService
from app.services.usuario.usuarios import UsuarioService
from app.services.compania.compania_servicio import CompaniaService
from app.services.cliente.cliente_servicio import ClienteService
from fastapi import HTTPException

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


    async def get_super_admin_dashboard(self, current_user: FirebaseUser):
        """
        Devuelve el resumen de usuarios, proyectos, usuarios, planes, etc.
        """
        usuario_service = UsuarioService(self.db)
        proyecto_service = ProyectoService(self.db)
        compania_service = CompaniaService(self.db)
        total_usuarios = await usuario_service.get_total_usuarios(usuario_actual=current_user)
        total_proyectos = await proyecto_service.get_total_proyectos(usuario_actual=current_user)
        total_companias = await compania_service.get_total_companias(usuario_actual=current_user)
        total_planes = 0

        return {
            "usuarios": total_usuarios,
            "proyectos": total_proyectos,
            "planes": total_planes,
            "companias": total_companias
        }
    
    async def get_admin_dashboard(self, current_user: FirebaseUser):
        """
        Devuelve el resumen de usuarios, proyectos, usuarios, planes, etc.
        """
        usuario_service = UsuarioService(self.db)
        proyecto_service = ProyectoService(self.db)
        orden_service = OrdenDeTrabajoService(self.db)
        cliente_service = ClienteService(self.db)
        unidad_service = UnidadService(self.db)

        total_usuarios = await usuario_service.get_total_usuarios(usuario_actual=current_user)
        total_proyectos = await proyecto_service.get_total_proyectos(usuario_actual=current_user)
        total_clientes = await cliente_service.get_total_clientes(usuario_actual=current_user)
        total_ordenes_trabajo = await orden_service.get_total_ordenes_trabajo_por_compania(company_id=current_user.company_id)
        total_unidades = await unidad_service.get_total_unidades_por_compania(company_id=current_user.company_id)

        return {
            "clientes": total_clientes,
            "proyectos": total_proyectos,
            "usuarios": total_usuarios,            
            "ordenes_trabajo": total_ordenes_trabajo,
            "unidades": total_unidades
        }
    
    async def get_supervisor_dashboard(self, current_user: FirebaseUser, year: Optional[int] = None, month: Optional[int] = None) -> SupervisorDashboard:
        """
        Devuelve el resumen de usuarios, proyectos, usuarios, planes, etc.
        """
        today = date.today()
        year = year or today.year
        month = month or today.month
        supervisor_uid = current_user.uid
        company_id = current_user.company_id

        stmt = select(
            func.count().label('total'),
            func.count().filter(OrdenDeTrabajo.estado_id == EstadoOrden.VALIDADA.value).label('validadas'),
            func.count().filter(OrdenDeTrabajo.estado_id == EstadoOrden.PENDIENTE.value).label('pendientes')
        ).where(
            and_(
                OrdenDeTrabajo.supervisor_id == supervisor_uid,
                OrdenDeTrabajo.company_id == company_id,
                extract("year", OrdenDeTrabajo.fecha) == year,
                extract("month", OrdenDeTrabajo.fecha) == month,
            )
        )
    
        result = await self.db.execute(stmt)
        row = result.first()
        return {
            "ordenes_trabajo": row.total,   
            "validadas": row.validadas,
            "pendientes": row.pendientes
        }
    
    async def get_tecnico_dashboard(self, current_user: FirebaseUser, year: Optional[int] = None, month: Optional[int] = None) -> TechnicianDashboard:
        """
        Devuelve el resumen de usuarios, proyectos, usuarios, planes, etc.
        """
        today = date.today()
        year = year or today.year
        month = month or today.month
        technician_uid = current_user.uid
        company_id = current_user.company_id

        stmt = select(
            func.count().label('total'),
            func.count().filter(OrdenDeTrabajo.estado_id == EstadoOrden.VALIDADA.value).label('validadas'),
            func.count().filter(OrdenDeTrabajo.estado_id == EstadoOrden.PENDIENTE.value).label('pendientes')
        ).where(
            and_(
                OrdenDeTrabajo.tecnico_id == technician_uid,
                OrdenDeTrabajo.company_id == company_id,
                extract("year", OrdenDeTrabajo.fecha) == year,
                extract("month", OrdenDeTrabajo.fecha) == month,
            )
        )

        result = await self.db.execute(stmt)
        row = result.first()
        return {
            "ordenes_trabajo": row.total,
            "validadas": row.validadas,
            "pendientes": row.pendientes
        }
    
    async def get_cliente_dashboard(self, current_user: FirebaseUser) -> ClienteDashboard:
        """
        Devuelve el resumen de usuarios, proyectos, usuarios, planes, etc.
        """
        cliente_id = current_user.uid
        if not cliente_id:
            raise HTTPException(status_code=403, detail="El usuario no puede acceder a este dashboard")
        
        proyecto_service = ProyectoService(self.db)
        unidad_service = UnidadService(self.db)
        orden_service = OrdenDeTrabajoService(self.db)
        proyectos = await proyecto_service.get_proyectos_by_cliente(cliente_id)

        data: List[ClienteDashboardProyecto] = []

        for proyecto in proyectos:
            cantidad_unidades = await unidad_service.get_total_unidades_por_proyecto(proyecto.id)
            cantidad_ordenes_activas = await orden_service.get_total_ordenes_trabajo_por_proyecto(proyecto.id)
            data.append(ClienteDashboardProyecto(
                nombre_proyecto=proyecto.nombre,
                estado=proyecto.estado.value,
                cantidad_unidades=cantidad_unidades,
                cantidad_ordenes_activas=cantidad_ordenes_activas,
                tiene_mantenimientos_por_vencer=False,
                fecha_de_vencimiento=None
            ))

        return ClienteDashboard(proyectos=data)
    
    