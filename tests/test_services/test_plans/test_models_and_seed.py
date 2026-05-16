import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Compania, CompanySubscription, CompanyUsage, Plan, TipoDocumento
from app.db.seeds.plans import PLAN_SEED_DATA, seed_plans
from app.db.session import AsyncSessionLocal


TEST_DOCUMENT_TYPE_ID = 991
TEST_COMPANY_DOCUMENT = "PLANS-TEST-COMPANY"
SEEDED_PLAN_CODES = [plan["code"] for plan in PLAN_SEED_DATA]


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.execute(
                delete(CompanySubscription).where(
                    CompanySubscription.company_id.in_(
                        select(Compania.id).where(Compania.documento == TEST_COMPANY_DOCUMENT)
                    )
                )
            )
            await session.execute(
                delete(CompanyUsage).where(
                    CompanyUsage.company_id.in_(
                        select(Compania.id).where(Compania.documento == TEST_COMPANY_DOCUMENT)
                    )
                )
            )
            await session.execute(delete(Plan).where(Plan.code.like("test-%")))
            await session.execute(delete(Compania).where(Compania.documento == TEST_COMPANY_DOCUMENT))
            await session.execute(delete(TipoDocumento).where(TipoDocumento.id == TEST_DOCUMENT_TYPE_ID))
            await session.commit()


async def _ensure_company(session: AsyncSession) -> Compania:
    document_type = await session.get(TipoDocumento, TEST_DOCUMENT_TYPE_ID)
    if document_type is None:
        document_type = TipoDocumento(
            id=TEST_DOCUMENT_TYPE_ID,
            nombre="Documento Test Planes",
            descripcion="Fixture temporal para planes",
        )
        session.add(document_type)
        await session.commit()

    company = (
        await session.execute(select(Compania).where(Compania.documento == TEST_COMPANY_DOCUMENT))
    ).scalars().first()
    if company is None:
        company = Compania(
            id=uuid.uuid4(),
            nombre="Compania Test Planes",
            documento=TEST_COMPANY_DOCUMENT,
            tipo_documento_id=TEST_DOCUMENT_TYPE_ID,
            email="planes@test.local",
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


@pytest.mark.asyncio
async def test_migration_creates_plans_related_tables(db_session: AsyncSession):
    for table_name in ("plans", "company_subscriptions", "company_usage"):
        result = await db_session.execute(select(func.to_regclass(f"public.{table_name}")))
        assert result.scalar_one() == table_name


@pytest.mark.asyncio
async def test_plan_model_can_be_created_and_queried(db_session: AsyncSession):
    plan = Plan(
        code="test-plan-basic",
        name="Test Plan Basic",
        description="Plan temporal de prueba",
        max_admins=1,
        is_public=False,
    )
    db_session.add(plan)
    await db_session.commit()

    fetched = (await db_session.execute(select(Plan).where(Plan.code == "test-plan-basic"))).scalars().one()

    assert fetched.name == "Test Plan Basic"
    assert fetched.max_admins == 1
    assert fetched.is_public is False


@pytest.mark.asyncio
async def test_plan_name_cannot_be_duplicated(db_session: AsyncSession):
    db_session.add(
        Plan(
            code="test-plan-duplicate-a",
            name="Test Plan Duplicate",
        )
    )
    await db_session.commit()

    db_session.add(
        Plan(
            code="test-plan-duplicate-b",
            name="Test Plan Duplicate",
        )
    )

    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_company_subscription_can_link_company_and_plan(db_session: AsyncSession):
    company = await _ensure_company(db_session)

    plan = Plan(
        code="test-plan-subscription",
        name="Test Plan Subscription",
        allow_offline_mode=True,
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)

    subscription = CompanySubscription(
        company_id=company.id,
        plan_id=plan.id,
        status="active",
        billing_period="monthly",
    )
    db_session.add(subscription)
    await db_session.commit()

    fetched = (
        await db_session.execute(
            select(CompanySubscription).where(CompanySubscription.id == subscription.id)
        )
    ).scalars().one()

    assert fetched.company_id == company.id
    assert fetched.plan_id == plan.id
    assert fetched.status == "active"


@pytest.mark.asyncio
async def test_company_usage_enforces_unique_company_period(db_session: AsyncSession):
    company = await _ensure_company(db_session)

    db_session.add(
        CompanyUsage(
            company_id=company.id,
            period_year=2026,
            period_month=5,
        )
    )
    await db_session.commit()

    db_session.add(
        CompanyUsage(
            company_id=company.id,
            period_year=2026,
            period_month=5,
        )
    )

    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_seed_plans_is_idempotent(db_session: AsyncSession):
    await seed_plans(db_session)

    starter = (await db_session.execute(select(Plan).where(Plan.code == "starter"))).scalars().one()
    starter.description = "descripcion temporal"
    starter.max_projects = 999
    await db_session.commit()

    await seed_plans(db_session)

    refreshed = (await db_session.execute(select(Plan).where(Plan.code == "starter"))).scalars().one()
    seeded_count = (
        await db_session.execute(select(func.count()).select_from(Plan).where(Plan.code.in_(SEEDED_PLAN_CODES)))
    ).scalar_one()

    assert refreshed.description == "Plan inicial para empresas pequeñas de mantenimiento"
    assert refreshed.max_projects == 10
    assert seeded_count == len(PLAN_SEED_DATA)


@pytest.mark.asyncio
async def test_seed_creates_expected_plans(db_session: AsyncSession):
    await seed_plans(db_session)

    rows = (
        await db_session.execute(select(Plan.code, Plan.name).where(Plan.code.in_(SEEDED_PLAN_CODES)))
    ).all()

    assert {row.code for row in rows} == set(SEEDED_PLAN_CODES)
    assert {row.name for row in rows} == {
        "Free",
        "Pilot Partner",
        "Starter",
        "Professional",
        "Enterprise",
    }
