from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.clientes import Cliente
from app.db.models.proyectos import Proyecto
from app.db.models.unidades import Unidad
from app.db.models.usuarios import Rol, Usuario
from app.services.plans.constants import (
    PLAN_LIMIT_REACHED_CODE,
    RESOURCE_LABELS,
)
from app.services.plans.plan_limits_service import PlanLimitService
from app.services.plans.plan_service import PlanService


NO_ACTIVE_SUBSCRIPTION_CODE = "NO_ACTIVE_SUBSCRIPTION"

USER_ROLE_RESOURCE_MAP = {
    Rol.ADMIN: "admins",
    Rol.SUPERVISOR: "supervisors",
    Rol.TECHNICIAN: "technicians",
}


class PlanEnforcementService:
    """Centralizes plan limit enforcement for resource creation flows."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.plan_service = PlanService(db)
        self.plan_limit_service = PlanLimitService(db)

    async def assert_can_create_user(self, company_id: UUID | None, role: Rol | str | None) -> None:
        resource = self._resource_for_user_role(role)
        if company_id is None or resource is None:
            return

        await self.assert_can_create_resource(company_id, resource)

    async def assert_can_create_client(self, company_id: UUID) -> None:
        await self.assert_can_create_resource(company_id, "clients")

    async def assert_can_create_project(self, company_id: UUID) -> None:
        await self.assert_can_create_resource(company_id, "projects")

    async def assert_can_create_unit(self, company_id: UUID) -> None:
        await self.assert_can_create_resource(company_id, "units")

    async def assert_can_create_resource(self, company_id: UUID, resource: str) -> None:
        plan = await self.plan_service.get_active_plan_for_company(company_id)
        if plan is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "La compania no tiene una suscripcion activa.",
                    "code": NO_ACTIVE_SUBSCRIPTION_CODE,
                    "resource": resource,
                },
            )

        current_usage = await self.count_current_usage(company_id, resource)
        result = await self.plan_limit_service.check_limit(
            company_id=company_id,
            resource=resource,
            current_usage=current_usage,
        )
        if result.allowed:
            return

        label = RESOURCE_LABELS.get(resource, resource)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": result.message or f"Has alcanzado el limite de {label} de tu plan.",
                "code": result.code or PLAN_LIMIT_REACHED_CODE,
                "resource": result.resource,
                "current_usage": result.current_usage,
                "plan_limit": result.plan_limit,
            },
        )

    async def count_current_usage(self, company_id: UUID, resource: str) -> int:
        if resource == "admins":
            return await self._count_users_by_role(company_id, Rol.ADMIN)
        if resource == "supervisors":
            return await self._count_users_by_role(company_id, Rol.SUPERVISOR)
        if resource == "technicians":
            return await self._count_users_by_role(company_id, Rol.TECHNICIAN)
        if resource == "clients":
            return await self._count(Cliente, Cliente.compania_id == company_id)
        if resource == "projects":
            return await self._count(Proyecto, Proyecto.company_id == company_id)
        if resource == "units":
            return await self._count(Unidad, Unidad.company_id == company_id)

        # Let PlanLimitService keep ownership of invalid resource validation.
        await self.plan_limit_service.get_limit(company_id, resource)
        return 0

    async def refresh_current_usage_snapshot(self, company_id: UUID) -> None:
        from app.services.plans.usage_service import CompanyUsageService

        today = datetime.now(timezone.utc).date()
        await CompanyUsageService(self.db).refresh_company_usage_snapshot(
            company_id=company_id,
            year=today.year,
            month=today.month,
        )

    async def _count_users_by_role(self, company_id: UUID, role: Rol) -> int:
        return await self._count(
            Usuario,
            Usuario.company_id == company_id,
            Usuario.rol == role,
            Usuario.is_active.is_(True),
        )

    async def _count(self, model, *filters) -> int:
        result = await self.db.execute(select(func.count()).select_from(model).where(*filters))
        return result.scalar_one() or 0

    def _resource_for_user_role(self, role: Rol | str | None) -> str | None:
        if isinstance(role, str):
            try:
                role = Rol(role)
            except ValueError:
                return None

        return USER_ROLE_RESOURCE_MAP.get(role)
