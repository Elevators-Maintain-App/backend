from datetime import date
from uuid import UUID

from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.overtime_requests import OvertimeRequest, OvertimeRequestEvent, OvertimeRequestStatus
from app.db.models.proyectos import Proyecto
from app.db.models.usuarios import Rol, Usuario
from app.schemas.proyectos import ProyectoEstado


class OvertimeRequestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_uid(self, uid: str) -> Usuario | None:
        result = await self.db.execute(select(Usuario).where(Usuario.uid == uid))
        return result.scalar_one_or_none()

    async def list_active_projects(self, company_id: UUID) -> list[Proyecto]:
        result = await self.db.execute(
            select(Proyecto)
            .where(Proyecto.company_id == company_id, Proyecto.estado == ProyectoEstado.ACTIVO)
            .order_by(Proyecto.nombre.asc())
        )
        return list(result.scalars().all())

    async def get_active_project(self, company_id: UUID, project_id: UUID) -> Proyecto | None:
        result = await self.db.execute(
            select(Proyecto).where(
                Proyecto.id == project_id,
                Proyecto.company_id == company_id,
                Proyecto.estado == ProyectoEstado.ACTIVO,
            )
        )
        return result.scalar_one_or_none()

    async def list_active_supervisors(self, company_id: UUID) -> list[Usuario]:
        result = await self.db.execute(
            select(Usuario)
            .where(
                Usuario.company_id == company_id,
                Usuario.rol == Rol.SUPERVISOR,
                Usuario.is_active.is_(True),
            )
            .order_by(Usuario.display_name.asc())
        )
        return list(result.scalars().all())

    async def get_active_supervisor(self, company_id: UUID, user_id: UUID) -> Usuario | None:
        result = await self.db.execute(
            select(Usuario).where(
                Usuario.id == user_id,
                Usuario.company_id == company_id,
                Usuario.rol == Rol.SUPERVISOR,
                Usuario.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def create_request(self, request: OvertimeRequest) -> OvertimeRequest:
        self.db.add(request)
        await self.db.flush()
        return request

    async def create_event(self, event: OvertimeRequestEvent) -> OvertimeRequestEvent:
        self.db.add(event)
        await self.db.flush()
        return event

    def _with_detail(self):
        return (
            selectinload(OvertimeRequest.project),
            selectinload(OvertimeRequest.technician),
            selectinload(OvertimeRequest.authorizing_supervisor),
            selectinload(OvertimeRequest.events),
        )

    async def list_for_technician(
        self, *, company_id: UUID, technician_id: UUID, status: OvertimeRequestStatus | None,
        date_from: date | None, date_to: date | None, skip: int, limit: int
    ) -> list[OvertimeRequest]:
        query = select(OvertimeRequest).where(
            OvertimeRequest.company_id == company_id,
            OvertimeRequest.technician_id == technician_id,
        ).options(*self._with_detail())
        if status is not None:
            query = query.where(OvertimeRequest.status == status)
        if date_from is not None:
            query = query.where(OvertimeRequest.work_date >= date_from)
        if date_to is not None:
            query = query.where(OvertimeRequest.work_date <= date_to)
        query = query.order_by(OvertimeRequest.work_date.desc(), OvertimeRequest.submitted_at.desc())
        result = await self.db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().unique().all())

    async def get_for_technician(
        self, *, request_id: UUID, company_id: UUID, technician_id: UUID
    ) -> OvertimeRequest | None:
        result = await self.db.execute(
            select(OvertimeRequest).where(
                OvertimeRequest.id == request_id,
                OvertimeRequest.company_id == company_id,
                OvertimeRequest.technician_id == technician_id,
            ).options(*self._with_detail())
        )
        return result.scalars().unique().one_or_none()

    async def list_for_supervisor(
        self, *, company_id: UUID, supervisor_id: UUID, status: OvertimeRequestStatus | None,
        technician_id: UUID | None, date_from: date | None, date_to: date | None,
        skip: int, limit: int
    ) -> list[OvertimeRequest]:
        query = select(OvertimeRequest).where(
            OvertimeRequest.company_id == company_id,
            OvertimeRequest.authorizing_supervisor_id == supervisor_id,
        ).options(*self._with_detail())
        if status is not None:
            query = query.where(OvertimeRequest.status == status)
        if technician_id is not None:
            query = query.where(OvertimeRequest.technician_id == technician_id)
        if date_from is not None:
            query = query.where(OvertimeRequest.work_date >= date_from)
        if date_to is not None:
            query = query.where(OvertimeRequest.work_date <= date_to)
        pending_first = case((OvertimeRequest.status == OvertimeRequestStatus.PENDING, 0), else_=1)
        query = query.order_by(pending_first, OvertimeRequest.work_date.desc(), OvertimeRequest.submitted_at.desc())
        result = await self.db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().unique().all())

    async def get_for_supervisor(
        self, *, request_id: UUID, company_id: UUID, supervisor_id: UUID
    ) -> OvertimeRequest | None:
        result = await self.db.execute(
            select(OvertimeRequest).where(
                OvertimeRequest.id == request_id,
                OvertimeRequest.company_id == company_id,
                OvertimeRequest.authorizing_supervisor_id == supervisor_id,
            ).options(*self._with_detail())
        )
        return result.scalars().unique().one_or_none()

    async def lock_for_supervisor_review(
        self, *, request_id: UUID, company_id: UUID, supervisor_id: UUID
    ) -> OvertimeRequest | None:
        result = await self.db.execute(
            select(OvertimeRequest).where(
                OvertimeRequest.id == request_id,
                OvertimeRequest.company_id == company_id,
                OvertimeRequest.authorizing_supervisor_id == supervisor_id,
            ).options(*self._with_detail()).with_for_update()
        )
        return result.scalars().unique().one_or_none()
