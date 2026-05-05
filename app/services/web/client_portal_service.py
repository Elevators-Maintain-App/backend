from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.auth.firebase import FirebaseUser
from app.db.models.checklists import Checklist
from app.db.models.clientes import Cliente
from app.db.models.enums.estados_orden import EstadoOrden
from app.db.models.enums.prioridades import Prioridad
from app.db.models.enums.tipos_orden import TipoOrden
from app.db.models.enums.tipos_unidad import TipoUnidad
from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.db.models.proyectos import Proyecto
from app.db.models.unidades import Unidad
from app.db.models.usuarios import Usuario
from app.schemas.web_client import (
    WebClientOrderDetail,
    WebClientOrderItem,
    WebClientOrdersPage,
    WebClientReportLink,
    WebClientUnitDetail,
    WebClientUnitItem,
    WebClientUnitsPage,
)


CLOSED_ORDER_STATUS = "Cerrada"


class WebClientPortalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_authorized_client(self, current_user: FirebaseUser) -> Cliente:
        if not current_user.client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El usuario cliente no tiene client_id asociado",
            )

        result = await self.db.execute(
            select(Cliente).where(
                Cliente.id == current_user.client_id,
                Cliente.compania_id == current_user.company_id,
            )
        )
        cliente = result.scalar_one_or_none()
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El cliente asociado no pertenece a la compania del usuario",
            )
        return cliente

    def _scope_filters(self, client_id: UUID, company_id: UUID):
        return (
            Proyecto.cliente_id == client_id,
            Proyecto.company_id == company_id,
            Unidad.company_id == company_id,
        )

    def _unit_base_query(self, client_id: UUID, company_id: UUID):
        return (
            select(
                Unidad.id.label("id"),
                Unidad.nombre.label("name"),
                Unidad.proyecto_id.label("project_id"),
                Unidad.kpi_funcionamiento.label("kpi_functioning"),
                Unidad.company_id.label("company_id"),
                Unidad.created_at.label("created_at"),
                Unidad.updated_at.label("updated_at"),
                Proyecto.nombre.label("project_name"),
                TipoUnidad.nombre.label("unit_type"),
            )
            .join(Proyecto, Unidad.proyecto_id == Proyecto.id)
            .join(TipoUnidad, Unidad.tipo_unidad_id == TipoUnidad.id)
            .where(*self._scope_filters(client_id, company_id))
        )

    def _apply_unit_filters(self, query, *, search: str | None, project_id: UUID | None):
        if search:
            value = f"%{search.strip()}%"
            query = query.where(or_(Unidad.nombre.ilike(value), Proyecto.nombre.ilike(value)))
        if project_id:
            query = query.where(Unidad.proyecto_id == project_id)
        return query

    def _to_unit_item(self, row):
        return WebClientUnitItem(
            id=row.id,
            name=row.name,
            project_id=row.project_id,
            project=row.project_name,
            type=row.unit_type,
            kpi_functioning=row.kpi_functioning,
        )

    async def get_units(
        self,
        current_user: FirebaseUser,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        project_id: UUID | None = None,
    ) -> WebClientUnitsPage:
        cliente = await self._get_authorized_client(current_user)
        normalized_search = search.strip() if search and search.strip() else None
        base_query = self._apply_unit_filters(
            self._unit_base_query(cliente.id, cliente.compania_id),
            search=normalized_search,
            project_id=project_id,
        )
        total_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(total_query)).scalar() or 0
        rows = (
            await self.db.execute(
                base_query.order_by(Proyecto.nombre.asc(), Unidad.nombre.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()

        return WebClientUnitsPage.create(
            data=[self._to_unit_item(row) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_unit_detail(
        self,
        current_user: FirebaseUser,
        unit_id: UUID,
    ) -> WebClientUnitDetail:
        cliente = await self._get_authorized_client(current_user)
        result = await self.db.execute(
            self._unit_base_query(cliente.id, cliente.compania_id).where(Unidad.id == unit_id)
        )
        row = result.one_or_none()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidad no encontrada")

        return WebClientUnitDetail(
            **self._to_unit_item(row).model_dump(),
            company_id=row.company_id,
            client_id=cliente.id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _order_report_url_expr(self):
        return func.max(Checklist.reporte_final_url)

    def _order_base_query(self, client_id: UUID, company_id: UUID):
        technician = aliased(Usuario)
        supervisor = aliased(Usuario)
        return (
            select(
                OrdenDeTrabajo.id.label("id"),
                OrdenDeTrabajo.referencia.label("reference"),
                OrdenDeTrabajo.fecha.label("date"),
                OrdenDeTrabajo.descripcion.label("description"),
                OrdenDeTrabajo.observaciones.label("observations"),
                OrdenDeTrabajo.tecnico_id.label("technician_id"),
                OrdenDeTrabajo.supervisor_id.label("supervisor_id"),
                OrdenDeTrabajo.created_at.label("created_at"),
                EstadoOrden.nombre.label("status_name"),
                TipoOrden.nombre.label("order_type"),
                Prioridad.nombre.label("priority_name"),
                Proyecto.id.label("project_id"),
                Proyecto.nombre.label("project_name"),
                Unidad.id.label("unit_id"),
                Unidad.nombre.label("unit_name"),
                technician.display_name.label("technician_name"),
                supervisor.display_name.label("supervisor_name"),
                self._order_report_url_expr().label("final_report_url"),
            )
            .join(Unidad, OrdenDeTrabajo.unidad_id == Unidad.id)
            .join(Proyecto, Unidad.proyecto_id == Proyecto.id)
            .join(EstadoOrden, OrdenDeTrabajo.estado_id == EstadoOrden.id)
            .join(TipoOrden, OrdenDeTrabajo.tipo_orden_id == TipoOrden.id)
            .join(Prioridad, OrdenDeTrabajo.prioridad_id == Prioridad.id)
            .outerjoin(Checklist, Checklist.orden_trabajo_id == OrdenDeTrabajo.id)
            .outerjoin(technician, technician.uid == OrdenDeTrabajo.tecnico_id)
            .outerjoin(supervisor, supervisor.uid == OrdenDeTrabajo.supervisor_id)
            .where(
                *self._scope_filters(client_id, company_id),
                OrdenDeTrabajo.company_id == company_id,
            )
            .group_by(
                OrdenDeTrabajo.id,
                OrdenDeTrabajo.referencia,
                OrdenDeTrabajo.fecha,
                OrdenDeTrabajo.descripcion,
                OrdenDeTrabajo.observaciones,
                OrdenDeTrabajo.tecnico_id,
                OrdenDeTrabajo.supervisor_id,
                OrdenDeTrabajo.created_at,
                EstadoOrden.nombre,
                TipoOrden.nombre,
                Prioridad.nombre,
                Proyecto.id,
                Proyecto.nombre,
                Unidad.id,
                Unidad.nombre,
                technician.display_name,
                supervisor.display_name,
            )
        )

    def _apply_order_filters(
        self,
        query,
        *,
        search: str | None,
        status_name: str | None,
        unit_id: UUID | None,
        project_id: UUID | None,
    ):
        if search:
            value = f"%{search.strip()}%"
            query = query.where(
                or_(
                    OrdenDeTrabajo.referencia.ilike(value),
                    OrdenDeTrabajo.descripcion.ilike(value),
                    Proyecto.nombre.ilike(value),
                    Unidad.nombre.ilike(value),
                )
            )
        if status_name:
            query = query.where(EstadoOrden.nombre == status_name)
        if unit_id:
            query = query.where(OrdenDeTrabajo.unidad_id == unit_id)
        if project_id:
            query = query.where(Unidad.proyecto_id == project_id)
        return query

    def _to_order_item(self, row) -> WebClientOrderItem:
        report_url = row.final_report_url if row.status_name == CLOSED_ORDER_STATUS else None
        return WebClientOrderItem(
            id=row.id,
            reference=row.reference,
            date=row.date,
            status=row.status_name,
            project_id=row.project_id,
            project=row.project_name,
            unit_id=row.unit_id,
            unit=row.unit_name,
            type=row.order_type,
            priority=row.priority_name,
            has_report=bool(report_url),
        )

    async def get_orders(
        self,
        current_user: FirebaseUser,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        status_name: str | None = None,
        unit_id: UUID | None = None,
        project_id: UUID | None = None,
    ) -> WebClientOrdersPage:
        cliente = await self._get_authorized_client(current_user)
        normalized_search = search.strip() if search and search.strip() else None
        normalized_status = status_name.strip() if status_name and status_name.strip() else None
        base_query = self._apply_order_filters(
            self._order_base_query(cliente.id, cliente.compania_id),
            search=normalized_search,
            status_name=normalized_status,
            unit_id=unit_id,
            project_id=project_id,
        )
        total = (await self.db.execute(select(func.count()).select_from(base_query.subquery()))).scalar() or 0
        rows = (
            await self.db.execute(
                base_query.order_by(
                    OrdenDeTrabajo.fecha.desc().nullslast(),
                    OrdenDeTrabajo.created_at.desc(),
                )
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
        return WebClientOrdersPage.create(
            data=[self._to_order_item(row) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_order_detail(
        self,
        current_user: FirebaseUser,
        order_id: UUID,
    ) -> WebClientOrderDetail:
        cliente = await self._get_authorized_client(current_user)
        result = await self.db.execute(
            self._order_base_query(cliente.id, cliente.compania_id).where(
                OrdenDeTrabajo.id == order_id
            )
        )
        row = result.one_or_none()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden no encontrada")

        item = self._to_order_item(row)
        final_report_url = row.final_report_url if row.status_name == CLOSED_ORDER_STATUS else None
        return WebClientOrderDetail(
            **item.model_dump(),
            description=row.description,
            observations=row.observations,
            technician=row.technician_name or row.technician_id,
            supervisor=row.supervisor_name or row.supervisor_id,
            final_report_url=final_report_url,
        )

    async def get_order_report(
        self,
        current_user: FirebaseUser,
        order_id: UUID,
    ) -> WebClientReportLink:
        order = await self.get_order_detail(current_user, order_id)
        if order.status != CLOSED_ORDER_STATUS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El reporte solo esta disponible para ordenes cerradas",
            )
        if not order.final_report_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No existe reporte final para esta orden",
            )
        return WebClientReportLink(report_url=order.final_report_url)
