from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.clientes import Cliente
from app.db.models.company_usage import CompanyUsage
from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
from app.db.models.pdf_report_generation_events import PdfReportGenerationEvent
from app.db.models.proyectos import Proyecto
from app.db.models.unidades import Unidad
from app.db.models.usuarios import Rol, Usuario
from app.db.repositories.company_usage import company_usage_repository


class CompanyUsageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_monthly_usage(
        self,
        company_id: UUID,
        year: int,
        month: int,
    ) -> CompanyUsage:
        if month < 1 or month > 12:
            raise ValueError("El mes debe estar entre 1 y 12.")

        usage = await company_usage_repository.get_by_company_period(self.db, company_id, year, month)
        if usage is not None:
            return usage

        usage = CompanyUsage(
            company_id=company_id,
            period_year=year,
            period_month=month,
        )
        self.db.add(usage)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            existing = await company_usage_repository.get_by_company_period(self.db, company_id, year, month)
            if existing is not None:
                return existing
            raise

        await self.db.refresh(usage)
        return usage

    async def refresh_company_usage_snapshot(
        self,
        company_id: UUID,
        year: int,
        month: int,
    ) -> CompanyUsage:
        usage = await self.get_or_create_monthly_usage(company_id, year, month)

        usage.users_count = await self._count_users(company_id)
        usage.admins_count = await self._count_users(company_id, Rol.ADMIN)
        usage.supervisors_count = await self._count_users(company_id, Rol.SUPERVISOR)
        usage.technicians_count = await self._count_users(company_id, Rol.TECHNICIAN)
        usage.projects_count = await self._count(Proyecto, Proyecto.company_id == company_id)
        usage.clients_count = await self._count(Cliente, Cliente.compania_id == company_id)
        usage.units_count = await self._count(Unidad, Unidad.company_id == company_id)
        usage.work_orders_created = await self._count_work_orders(company_id, year, month)
        usage.pdf_reports_generated = await self._count_pdf_reports(company_id, year, month)

        self.db.add(usage)
        await self.db.commit()
        await self.db.refresh(usage)
        return usage

    async def _count_users(self, company_id: UUID, role: Rol | None = None) -> int:
        filters = [
            Usuario.company_id == company_id,
            Usuario.is_active.is_(True),
        ]
        if role is not None:
            filters.append(Usuario.rol == role)

        return await self._count(Usuario, *filters)

    async def _count(self, model, *filters) -> int:
        result = await self.db.execute(select(func.count()).select_from(model).where(*filters))
        return result.scalar_one() or 0

    async def _count_work_orders(self, company_id: UUID, year: int, month: int) -> int:
        start, end = self._month_bounds(year, month)
        return await self._count(
            OrdenDeTrabajo,
            OrdenDeTrabajo.company_id == company_id,
            OrdenDeTrabajo.created_at >= start,
            OrdenDeTrabajo.created_at < end,
        )

    async def _count_pdf_reports(self, company_id: UUID, year: int, month: int) -> int:
        start, end = self._month_bounds(year, month)
        return await self._count(
            PdfReportGenerationEvent,
            PdfReportGenerationEvent.company_id == company_id,
            PdfReportGenerationEvent.status == "success",
            PdfReportGenerationEvent.created_at >= start,
            PdfReportGenerationEvent.created_at < end,
        )

    def _month_bounds(self, year: int, month: int):
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        return start, end
