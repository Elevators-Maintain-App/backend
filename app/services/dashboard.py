# app/services/dashboard.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.db.models.unidades import Unidad
from app.db.models.hojas_de_vida import HojaDeVida
from app.db.models.usuarios import Usuario
from app.db.models.compania import Compania
from app.db.models.proyectos import Proyecto
from app.db.models.clientes import Cliente


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


    async def get_super_admin_dashboard(self):
        """
        Devuelve el resumen de usuarios, proyectos, usuarios, planes, etc.
        """
        total_usuarios = select(func.count(Usuario.id)).where(Usuario.is_active == True).scalar_subquery()
        total_proyectos = select(func.count(Proyecto.id)).scalar_subquery()
        total_companias = select(func.count(Compania.id)).scalar_subquery()
        total_planes = 0

        query = select(
            total_usuarios.label("total_usuarios"),
            total_proyectos.label("total_proyectos"),
            total_companias.label("total_companias")
        )

        result = await self.db.execute(query)
        summary = result.fetchone()

        return {
            "usuarios": summary.total_usuarios,
            "proyectos": summary.total_proyectos,
            "planes": total_planes,
            "companias": summary.total_companias
        }
    
    async def get_admin_dashboard(self, current_company_id: str):
        """
        Devuelve el resumen de usuarios, proyectos, usuarios, planes, etc.
        """

        total_usuarios = select(func.count(Usuario.id)).where(Usuario.is_active == True, Usuario.company_id == current_company_id).scalar_subquery()
        total_proyectos = select(func.count(Proyecto.id)).where(Proyecto.company_id == current_company_id).scalar_subquery()
        total_clientes = select(func.count(Cliente.id)).where(Cliente.company_id == current_company_id).scalar_subquery()
        total_ordenes_trabajo = select(func.count(OrdenDeTrabajo.id)).where(OrdenDeTrabajo.company_id == current_company_id).scalar_subquery()
        total_unidades = select(func.count(Unidad.id)).where(Unidad.company_id == current_company_id).scalar_subquery()

        query = select(
            total_clientes.label("total_clientes"),
            total_proyectos.label("total_proyectos"),
            total_usuarios.label("total_usuarios"),
            total_ordenes_trabajo.label("total_ordenes_trabajo"),
            total_unidades.label("total_unidades")
        )

        result = await self.db.execute(query)
        summary = result.fetchone()
        
        return {
            "clientes": summary.total_clientes,
            "proyectos": summary.total_proyectos,
            "usuarios": summary.total_usuarios,            
            "ordenes_trabajo": summary.total_ordenes_trabajo,
            "unidades": summary.total_unidades
        }
    
    async def get_supervisor_dashboard(self):
        """
        Devuelve el resumen de usuarios, proyectos, usuarios, planes, etc.
        """
        return {
            "usuarios": 0,
            "proyectos": 0,
            "planes": 0,
            "companias": 0
        }
    
    async def get_cliente_dashboard(self):
        """
        Devuelve el resumen de usuarios, proyectos, usuarios, planes, etc.
        """
        return {
            "usuarios": 0,
            "proyectos": 0,
            "planes": 0,
            "companias": 0
        }
    
    async def get_tecnico_dashboard(self):
        """
        Devuelve el resumen de usuarios, proyectos, usuarios, planes, etc.
        """
        return {
            "usuarios": 0,
            "proyectos": 0,
            "planes": 0,
            "companias": 0
        }