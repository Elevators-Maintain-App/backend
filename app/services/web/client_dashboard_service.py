from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.firebase import FirebaseUser
from app.db.models.clientes import Cliente
from app.db.models.enums.estados_orden import EstadoOrden
from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.db.models.proyectos import Proyecto
from app.db.models.unidades import Unidad
from app.schemas.web_client import (
    WebClientDashboard,
    WebClientDashboardSummary,
    WebClientInfo,
    WebClientRecentOrder,
)


CLOSED_ORDER_STATUS = "Cerrada"


class WebClientDashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_authorized_client(self, current_user: FirebaseUser) -> Cliente:
        if not current_user.client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El usuario cliente no tiene client_id asociado",
            )

        query = select(Cliente).where(
            Cliente.id == current_user.client_id,
            Cliente.compania_id == current_user.company_id,
        )
        result = await self.db.execute(query)
        cliente = result.scalar_one_or_none()
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El cliente asociado no pertenece a la compania del usuario",
            )
        return cliente

    def _client_project_filters(self, client_id: UUID, company_id: UUID):
        return (
            Proyecto.cliente_id == client_id,
            Proyecto.company_id == company_id,
        )

    async def _count_projects(self, client_id: UUID, company_id: UUID) -> int:
        query = select(func.count()).select_from(Proyecto).where(
            *self._client_project_filters(client_id, company_id)
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _count_units(self, client_id: UUID, company_id: UUID) -> int:
        query = (
            select(func.count())
            .select_from(Unidad)
            .join(Proyecto, Unidad.proyecto_id == Proyecto.id)
            .where(*self._client_project_filters(client_id, company_id))
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _count_orders(
        self,
        client_id: UUID,
        company_id: UUID,
        *,
        closed: bool,
    ) -> int:
        status_filter = (
            EstadoOrden.nombre == CLOSED_ORDER_STATUS
            if closed
            else EstadoOrden.nombre != CLOSED_ORDER_STATUS
        )
        query = (
            select(func.count())
            .select_from(OrdenDeTrabajo)
            .join(Unidad, OrdenDeTrabajo.unidad_id == Unidad.id)
            .join(Proyecto, Unidad.proyecto_id == Proyecto.id)
            .join(EstadoOrden, OrdenDeTrabajo.estado_id == EstadoOrden.id)
            .where(
                *self._client_project_filters(client_id, company_id),
                OrdenDeTrabajo.company_id == company_id,
                status_filter,
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _recent_orders(
        self,
        client_id: UUID,
        company_id: UUID,
    ) -> list[WebClientRecentOrder]:
        query = (
            select(
                OrdenDeTrabajo.id,
                OrdenDeTrabajo.referencia,
                OrdenDeTrabajo.fecha,
                EstadoOrden.nombre.label("status"),
                Unidad.nombre.label("unit"),
                Proyecto.nombre.label("project"),
            )
            .select_from(OrdenDeTrabajo)
            .join(Unidad, OrdenDeTrabajo.unidad_id == Unidad.id)
            .join(Proyecto, Unidad.proyecto_id == Proyecto.id)
            .join(EstadoOrden, OrdenDeTrabajo.estado_id == EstadoOrden.id)
            .where(
                *self._client_project_filters(client_id, company_id),
                OrdenDeTrabajo.company_id == company_id,
            )
            .order_by(OrdenDeTrabajo.fecha.desc(), OrdenDeTrabajo.created_at.desc())
            .limit(5)
        )
        result = await self.db.execute(query)
        return [
            WebClientRecentOrder(
                id=row.id,
                reference=row.referencia,
                date=row.fecha,
                status=row.status,
                unit=row.unit,
                project=row.project,
            )
            for row in result.all()
        ]

    async def get_dashboard(self, current_user: FirebaseUser) -> WebClientDashboard:
        cliente = await self._get_authorized_client(current_user)
        client_id = cliente.id
        company_id = cliente.compania_id

        # Estado cerrado: el backend usa el catalogo estados_orden; "Cerrada"
        # es el estado de cierre observado en dashboards existentes.
        total_projects = await self._count_projects(client_id, company_id)
        total_units = await self._count_units(client_id, company_id)
        open_orders = await self._count_orders(client_id, company_id, closed=False)
        closed_orders = await self._count_orders(client_id, company_id, closed=True)
        recent_orders = await self._recent_orders(client_id, company_id)

        return WebClientDashboard(
            client=WebClientInfo(id=cliente.id, name=cliente.nombre or ""),
            summary=WebClientDashboardSummary(
                total_projects=total_projects,
                total_units=total_units,
                open_orders=open_orders,
                closed_orders=closed_orders,
            ),
            recent_orders=recent_orders,
        )
