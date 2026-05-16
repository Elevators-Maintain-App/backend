from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.compania import Compania
from app.db.models.company_subscriptions import CompanySubscription
from app.db.models.plans import Plan
from app.services.plans.constants import ACTIVE_SUBSCRIPTION_STATUSES


PLAN_SEED_DATA = [
    {
        "code": "free",
        "name": "Free",
        "description": "Plan base temporal sin limites para compatibilidad de companias existentes",
        "max_admins": None,
        "max_supervisors": None,
        "max_technicians": None,
        "max_projects": None,
        "max_clients": None,
        "max_units": None,
        "max_work_orders_per_month": None,
        "max_pdf_reports_per_month": None,
        "storage_limit_mb": None,
        "allow_offline_mode": True,
        "allow_custom_checklists": True,
        "allow_advanced_dashboard": True,
        "allow_evidence_editing": True,
        "is_public": True,
        "is_active": True,
    },
    {
        "code": "pilot_partner",
        "name": "Pilot Partner",
        "description": "Plan piloto colaborativo con límites ampliados y acompañamiento personalizado",
        "max_admins": 2,
        "max_supervisors": 3,
        "max_technicians": 10,
        "max_projects": 10,
        "max_clients": 20,
        "max_units": 100,
        "max_work_orders_per_month": 500,
        "max_pdf_reports_per_month": 500,
        "storage_limit_mb": 5000,
        "allow_offline_mode": True,
        "allow_custom_checklists": True,
        "allow_advanced_dashboard": True,
        "allow_evidence_editing": True,
        "is_public": True,
        "is_active": True,
    },
    {
        "code": "starter",
        "name": "Starter",
        "description": "Plan inicial para empresas pequeñas de mantenimiento",
        "max_admins": 2,
        "max_supervisors": 3,
        "max_technicians": 8,
        "max_projects": 10,
        "max_clients": 30,
        "max_units": 150,
        "max_work_orders_per_month": 400,
        "max_pdf_reports_per_month": 400,
        "storage_limit_mb": 3000,
        "allow_offline_mode": True,
        "allow_custom_checklists": False,
        "allow_advanced_dashboard": False,
        "allow_evidence_editing": False,
        "is_public": True,
        "is_active": True,
    },
    {
        "code": "professional",
        "name": "Professional",
        "description": "Plan profesional para operación técnica en crecimiento",
        "max_admins": 5,
        "max_supervisors": 10,
        "max_technicians": 50,
        "max_projects": 50,
        "max_clients": 150,
        "max_units": 1000,
        "max_work_orders_per_month": 3000,
        "max_pdf_reports_per_month": 3000,
        "storage_limit_mb": 25000,
        "allow_offline_mode": True,
        "allow_custom_checklists": True,
        "allow_advanced_dashboard": True,
        "allow_evidence_editing": True,
        "is_public": True,
        "is_active": True,
    },
    {
        "code": "enterprise",
        "name": "Enterprise",
        "description": "Plan empresarial con límites personalizados",
        "max_admins": None,
        "max_supervisors": None,
        "max_technicians": None,
        "max_projects": None,
        "max_clients": None,
        "max_units": None,
        "max_work_orders_per_month": None,
        "max_pdf_reports_per_month": None,
        "storage_limit_mb": None,
        "allow_offline_mode": True,
        "allow_custom_checklists": True,
        "allow_advanced_dashboard": True,
        "allow_evidence_editing": True,
        "is_public": True,
        "is_active": True,
    },
]


async def seed_plans(db: AsyncSession) -> list[Plan]:
    created_or_updated: list[Plan] = []

    for plan_data in PLAN_SEED_DATA:
        existing = await db.execute(select(Plan).where(Plan.code == plan_data["code"]))
        plan = existing.scalars().first()

        if plan is None:
            plan = Plan(**plan_data)
            db.add(plan)
        else:
            for field, value in plan_data.items():
                setattr(plan, field, value)

        created_or_updated.append(plan)

    await db.commit()

    for plan in created_or_updated:
        await db.refresh(plan)

    return created_or_updated


def _subscription_is_active(subscription: CompanySubscription, today: date) -> bool:
    status = (subscription.status or "").lower()
    if status not in ACTIVE_SUBSCRIPTION_STATUSES:
        return False
    if subscription.start_date and subscription.start_date > today:
        return False
    if subscription.end_date and subscription.end_date < today:
        return False
    return True


async def backfill_free_subscriptions(db: AsyncSession) -> list[CompanySubscription]:
    await seed_plans(db)

    free_plan = (
        await db.execute(select(Plan).where(Plan.code == "free"))
    ).scalars().one()

    companies = (await db.execute(select(Compania))).scalars().all()
    subscriptions = (await db.execute(select(CompanySubscription))).scalars().all()
    today = date.today()

    subscriptions_by_company: dict = {}
    for subscription in subscriptions:
        subscriptions_by_company.setdefault(subscription.company_id, []).append(subscription)

    created: list[CompanySubscription] = []
    for company in companies:
        company_subscriptions = subscriptions_by_company.get(company.id, [])
        has_active_subscription = any(
            _subscription_is_active(subscription, today)
            for subscription in company_subscriptions
        )
        if has_active_subscription:
            continue

        subscription = CompanySubscription(
            company_id=company.id,
            plan_id=free_plan.id,
            status="active",
            billing_period="monthly",
            start_date=today,
            end_date=None,
        )
        db.add(subscription)
        created.append(subscription)

    await db.commit()
    for subscription in created:
        await db.refresh(subscription)

    return created


async def seed_plans_and_company_subscriptions(db: AsyncSession) -> list[CompanySubscription]:
    return await backfill_free_subscriptions(db)


async def _run() -> None:
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        await seed_plans_and_company_subscriptions(session)


if __name__ == "__main__":
    import asyncio

    asyncio.run(_run())
