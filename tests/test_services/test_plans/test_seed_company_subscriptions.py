import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Compania, CompanySubscription, Plan, TipoDocumento
from app.db.seeds.plans import (
    backfill_free_subscriptions,
    seed_plans,
    seed_plans_and_company_subscriptions,
)
from app.db.session import AsyncSessionLocal


TEST_DOCUMENT_TYPE_ID = 994
TEST_COMPANY_DOCUMENT_PREFIX = "PLANS-BACKFILL-TEST"
FREE_LIMIT_FIELDS = [
    "max_admins",
    "max_supervisors",
    "max_technicians",
    "max_projects",
    "max_clients",
    "max_units",
    "max_work_orders_per_month",
    "max_pdf_reports_per_month",
    "storage_limit_mb",
]


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            test_company_ids = select(Compania.id).where(
                Compania.documento.like(f"{TEST_COMPANY_DOCUMENT_PREFIX}%")
            )
            await session.execute(
                delete(CompanySubscription).where(CompanySubscription.company_id.in_(test_company_ids))
            )
            await session.execute(delete(Plan).where(Plan.code.like("test-backfill-%")))
            await session.execute(
                delete(Compania).where(Compania.documento.like(f"{TEST_COMPANY_DOCUMENT_PREFIX}%"))
            )
            await session.execute(delete(TipoDocumento).where(TipoDocumento.id == TEST_DOCUMENT_TYPE_ID))
            await session.commit()


async def _ensure_document_type(session: AsyncSession) -> None:
    document_type = await session.get(TipoDocumento, TEST_DOCUMENT_TYPE_ID)
    if document_type is None:
        session.add(
            TipoDocumento(
                id=TEST_DOCUMENT_TYPE_ID,
                nombre="Documento Test Backfill Planes",
                descripcion="Fixture temporal para backfill de planes",
            )
        )
        await session.commit()


async def _create_company(session: AsyncSession, suffix: str) -> Compania:
    await _ensure_document_type(session)
    company = Compania(
        id=uuid.uuid4(),
        nombre=f"Compania Backfill {suffix}",
        documento=f"{TEST_COMPANY_DOCUMENT_PREFIX}-{suffix}",
        tipo_documento_id=TEST_DOCUMENT_TYPE_ID,
        email=f"backfill-{suffix}@test.local",
        telefono="0000000",
        pais_id=None,
        ciudad="Test City",
        direccion="Test Address",
        logo=None,
    )
    session.add(company)
    await session.commit()
    await session.refresh(company)
    return company


async def _get_free_plan(session: AsyncSession) -> Plan:
    return (await session.execute(select(Plan).where(Plan.code == "free"))).scalars().one()


@pytest.mark.asyncio
async def test_seed_creates_free_plan_if_missing(db_session: AsyncSession):
    existing_free = (await db_session.execute(select(Plan).where(Plan.code == "free"))).scalars().first()
    if existing_free is not None:
        await db_session.execute(delete(CompanySubscription).where(CompanySubscription.plan_id == existing_free.id))
        await db_session.execute(delete(Plan).where(Plan.id == existing_free.id))
        await db_session.commit()

    await seed_plans(db_session)

    free_plan = await _get_free_plan(db_session)
    assert free_plan.code == "free"
    assert free_plan.name == "Free"
    assert free_plan.is_active is True
    assert free_plan.is_public is True


@pytest.mark.asyncio
async def test_seed_updates_existing_free_plan_without_duplicate(db_session: AsyncSession):
    await seed_plans(db_session)
    free_plan = await _get_free_plan(db_session)
    free_plan.max_admins = 1
    free_plan.max_projects = 1
    free_plan.allow_custom_checklists = False
    await db_session.commit()

    await seed_plans(db_session)

    refreshed = await _get_free_plan(db_session)
    free_count = (
        await db_session.execute(select(func.count()).select_from(Plan).where(Plan.code == "free"))
    ).scalar_one()
    assert free_count == 1
    assert refreshed.max_admins is None
    assert refreshed.max_projects is None
    assert refreshed.allow_custom_checklists is True


@pytest.mark.asyncio
async def test_free_plan_has_no_limits_and_features_enabled(db_session: AsyncSession):
    await seed_plans(db_session)

    free_plan = await _get_free_plan(db_session)

    for field in FREE_LIMIT_FIELDS:
        assert getattr(free_plan, field) is None
    assert free_plan.allow_offline_mode is True
    assert free_plan.allow_custom_checklists is True
    assert free_plan.allow_advanced_dashboard is True
    assert free_plan.allow_evidence_editing is True


@pytest.mark.asyncio
async def test_backfill_creates_active_free_subscription_for_company_without_active_subscription(db_session: AsyncSession):
    company = await _create_company(db_session, "NO-SUB")

    created = await backfill_free_subscriptions(db_session)

    free_plan = await _get_free_plan(db_session)
    subscription = (
        await db_session.execute(
            select(CompanySubscription).where(CompanySubscription.company_id == company.id)
        )
    ).scalars().one()
    assert any(item.company_id == company.id for item in created)
    assert subscription.plan_id == free_plan.id
    assert subscription.status == "active"
    assert subscription.billing_period == "monthly"
    assert subscription.end_date is None


@pytest.mark.asyncio
async def test_backfill_does_not_create_subscription_for_company_with_active_subscription(db_session: AsyncSession):
    company = await _create_company(db_session, "ACTIVE-SUB")
    paid_plan = Plan(
        code=f"test-backfill-paid-{uuid.uuid4()}",
        name=f"Test Backfill Paid {uuid.uuid4()}",
        is_active=True,
        is_public=False,
    )
    db_session.add(paid_plan)
    await db_session.commit()
    await db_session.refresh(paid_plan)
    active_subscription = CompanySubscription(
        company_id=company.id,
        plan_id=paid_plan.id,
        status="active",
        billing_period="monthly",
    )
    db_session.add(active_subscription)
    await db_session.commit()

    await backfill_free_subscriptions(db_session)

    subscriptions = (
        await db_session.execute(
            select(CompanySubscription).where(CompanySubscription.company_id == company.id)
        )
    ).scalars().all()
    assert len(subscriptions) == 1
    assert subscriptions[0].plan_id == paid_plan.id
    assert subscriptions[0].status == "active"


@pytest.mark.asyncio
async def test_backfill_is_idempotent_for_same_company(db_session: AsyncSession):
    company = await _create_company(db_session, "IDEMPOTENT")

    await seed_plans_and_company_subscriptions(db_session)
    await seed_plans_and_company_subscriptions(db_session)

    count = (
        await db_session.execute(
            select(func.count())
            .select_from(CompanySubscription)
            .where(CompanySubscription.company_id == company.id)
        )
    ).scalar_one()
    assert count == 1


@pytest.mark.asyncio
async def test_backfill_assigns_free_to_all_companies_without_active_subscription(db_session: AsyncSession):
    company_one = await _create_company(db_session, "MULTI-ONE")
    company_two = await _create_company(db_session, "MULTI-TWO")

    await backfill_free_subscriptions(db_session)

    rows = (
        await db_session.execute(
            select(CompanySubscription).where(
                CompanySubscription.company_id.in_([company_one.id, company_two.id])
            )
        )
    ).scalars().all()
    assert {row.company_id for row in rows} == {company_one.id, company_two.id}
    assert all(row.status == "active" for row in rows)


@pytest.mark.asyncio
async def test_backfill_respects_companies_with_active_subscription_while_filling_others(db_session: AsyncSession):
    company_with_subscription = await _create_company(db_session, "RESPECT-ACTIVE")
    company_without_subscription = await _create_company(db_session, "FILL-MISSING")
    paid_plan = Plan(
        code=f"test-backfill-existing-{uuid.uuid4()}",
        name=f"Test Backfill Existing {uuid.uuid4()}",
        is_active=True,
        is_public=False,
    )
    db_session.add(paid_plan)
    await db_session.commit()
    await db_session.refresh(paid_plan)
    db_session.add(
        CompanySubscription(
            company_id=company_with_subscription.id,
            plan_id=paid_plan.id,
            status="active",
            billing_period="monthly",
        )
    )
    await db_session.commit()

    await backfill_free_subscriptions(db_session)

    rows = (
        await db_session.execute(
            select(CompanySubscription).where(
                CompanySubscription.company_id.in_([
                    company_with_subscription.id,
                    company_without_subscription.id,
                ])
            )
        )
    ).scalars().all()
    by_company = {row.company_id: row for row in rows}
    free_plan = await _get_free_plan(db_session)

    assert by_company[company_with_subscription.id].plan_id == paid_plan.id
    assert by_company[company_without_subscription.id].plan_id == free_plan.id
