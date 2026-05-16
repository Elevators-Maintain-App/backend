import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Compania, CompanySubscription, CompanyUsage, Plan, TipoDocumento
from app.db.session import AsyncSessionLocal
from app.services.plans import (
    CompanyUsageService,
    InvalidPlanFeatureError,
    InvalidPlanResourceError,
    PlanLimitService,
    PlanService,
    SubscriptionService,
)
from app.services.plans.constants import PLAN_LIMIT_REACHED_CODE


TEST_DOCUMENT_TYPE_ID = 992
TEST_COMPANY_DOCUMENT = "PLANS-SERVICE-TEST-COMPANY"


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            company_ids = select(Compania.id).where(Compania.documento == TEST_COMPANY_DOCUMENT)
            await session.execute(delete(CompanySubscription).where(CompanySubscription.company_id.in_(company_ids)))
            await session.execute(delete(CompanyUsage).where(CompanyUsage.company_id.in_(company_ids)))
            await session.execute(delete(Plan).where(Plan.code.like("test-slice2-%")))
            await session.execute(delete(Compania).where(Compania.documento == TEST_COMPANY_DOCUMENT))
            await session.execute(delete(TipoDocumento).where(TipoDocumento.id == TEST_DOCUMENT_TYPE_ID))
            await session.commit()


async def _create_company(session: AsyncSession) -> Compania:
    document_type = await session.get(TipoDocumento, TEST_DOCUMENT_TYPE_ID)
    if document_type is None:
        document_type = TipoDocumento(
            id=TEST_DOCUMENT_TYPE_ID,
            nombre="Documento Test Servicios Planes",
            descripcion="Fixture temporal para servicios de planes",
        )
        session.add(document_type)
        await session.commit()

    company = Compania(
        id=uuid.uuid4(),
        nombre="Compania Servicios Planes",
        documento=TEST_COMPANY_DOCUMENT,
        tipo_documento_id=TEST_DOCUMENT_TYPE_ID,
        email="planes-services@test.local",
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


async def _create_plan(session: AsyncSession, **overrides) -> Plan:
    plan_data = {
        "code": f"test-slice2-{uuid.uuid4()}",
        "name": f"Test Slice 2 Plan {uuid.uuid4()}",
        "max_technicians": 2,
        "max_projects": 5,
        "storage_limit_mb": None,
        "allow_offline_mode": True,
        "allow_custom_checklists": False,
        "allow_advanced_dashboard": True,
        "allow_evidence_editing": False,
        "is_active": True,
        "is_public": False,
    }
    plan_data.update(overrides)
    plan = Plan(**plan_data)
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan


async def _create_subscription(
    session: AsyncSession,
    company: Compania,
    plan: Plan,
    *,
    status: str = "active",
    start_date: date | None = None,
    end_date: date | None = None,
) -> CompanySubscription:
    subscription = CompanySubscription(
        company_id=company.id,
        plan_id=plan.id,
        status=status,
        billing_period="monthly",
        start_date=start_date or date.today() - timedelta(days=1),
        end_date=end_date,
    )
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription)
    return subscription


@pytest.mark.asyncio
async def test_get_active_plan_for_company_with_active_subscription(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, code="test-slice2-active-plan", name="Test Slice 2 Active Plan")
    await _create_subscription(db_session, company, plan)

    active_plan = await PlanService(db_session).get_active_plan_for_company(company.id)

    assert active_plan is not None
    assert active_plan.id == plan.id


@pytest.mark.asyncio
async def test_get_active_subscription_returns_none_when_company_has_no_active_subscription(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session)
    await _create_subscription(db_session, company, plan, status="suspended")

    subscription = await SubscriptionService(db_session).get_active_subscription(company.id)
    active_plan = await PlanService(db_session).get_active_plan_for_company(company.id)

    assert subscription is None
    assert active_plan is None


@pytest.mark.asyncio
async def test_get_active_subscription_ignores_expired_subscription(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session)
    await _create_subscription(
        db_session,
        company,
        plan,
        status="active",
        start_date=date.today() - timedelta(days=10),
        end_date=date.today() - timedelta(days=1),
    )

    subscription = await SubscriptionService(db_session).get_active_subscription(company.id)

    assert subscription is None


@pytest.mark.asyncio
async def test_get_or_create_monthly_usage_creates_zero_usage_and_reuses_it(db_session: AsyncSession):
    company = await _create_company(db_session)
    service = CompanyUsageService(db_session)

    created = await service.get_or_create_monthly_usage(company.id, 2026, 5)
    reused = await service.get_or_create_monthly_usage(company.id, 2026, 5)

    assert created.id == reused.id
    assert reused.work_orders_created == 0
    assert reused.pdf_reports_generated == 0
    assert reused.storage_used_mb == 0


@pytest.mark.asyncio
async def test_get_limit_for_valid_resource(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_technicians=3)
    await _create_subscription(db_session, company, plan)

    limit = await PlanLimitService(db_session).get_limit(company.id, "technicians")

    assert limit == 3


@pytest.mark.asyncio
async def test_is_feature_enabled_for_valid_feature(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, allow_offline_mode=True)
    await _create_subscription(db_session, company, plan)

    allowed = await PlanLimitService(db_session).is_feature_enabled(company.id, "offline_mode")

    assert allowed is True


@pytest.mark.asyncio
async def test_check_limit_allows_usage_below_limit(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_technicians=2)
    await _create_subscription(db_session, company, plan)

    result = await PlanLimitService(db_session).check_limit(company.id, "technicians", current_usage=1)

    assert result.allowed is True
    assert result.resource == "technicians"
    assert result.current_usage == 1
    assert result.plan_limit == 2
    assert result.code is None
    assert result.message is None


@pytest.mark.asyncio
async def test_check_limit_blocks_usage_at_or_above_limit(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_technicians=2)
    await _create_subscription(db_session, company, plan)

    result = await PlanLimitService(db_session).check_limit(company.id, "technicians", current_usage=2)

    assert result.allowed is False
    assert result.resource == "technicians"
    assert result.current_usage == 2
    assert result.plan_limit == 2
    assert result.code == PLAN_LIMIT_REACHED_CODE
    assert result.message == "Has alcanzado el limite de tecnicos de tu plan actual."


@pytest.mark.asyncio
async def test_check_limit_allows_unlimited_resource(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, storage_limit_mb=None)
    await _create_subscription(db_session, company, plan)

    result = await PlanLimitService(db_session).check_limit(company.id, "storage_mb", current_usage=999999)

    assert result.allowed is True
    assert result.plan_limit is None


@pytest.mark.asyncio
async def test_invalid_resource_key_raises_controlled_error(db_session: AsyncSession):
    company = await _create_company(db_session)

    with pytest.raises(InvalidPlanResourceError) as exc_info:
        await PlanLimitService(db_session).get_limit(company.id, "unknown_resource")

    assert exc_info.value.code == "INVALID_PLAN_RESOURCE"
    assert exc_info.value.resource == "unknown_resource"


@pytest.mark.asyncio
async def test_invalid_feature_key_raises_controlled_error(db_session: AsyncSession):
    company = await _create_company(db_session)

    with pytest.raises(InvalidPlanFeatureError) as exc_info:
        await PlanLimitService(db_session).is_feature_enabled(company.id, "unknown_feature")

    assert exc_info.value.code == "INVALID_PLAN_FEATURE"
    assert exc_info.value.feature == "unknown_feature"
