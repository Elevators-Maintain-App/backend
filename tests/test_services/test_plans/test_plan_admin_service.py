import uuid
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Compania, CompanySubscription, Plan, TipoDocumento
from app.db.session import AsyncSessionLocal
from app.schemas.plans import PlanCreate, PlanUpdate
from app.services.plans import (
    FreePlanCannotBeDeactivatedError,
    InvalidPlanPayloadError,
    PlanAdminService,
    PlanCodeAlreadyExistsError,
    PlanHasActiveSubscriptionsError,
    PlanNotFoundError,
)


TEST_DOCUMENT_TYPE_ID = 996
TEST_COMPANY_DOCUMENT = "PLAN-ADMIN-SERVICE-COMPANY"


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            company_ids = select(Compania.id).where(Compania.documento == TEST_COMPANY_DOCUMENT)
            plan_ids = select(Plan.id).where(Plan.code.like("test-admin-service-%"))
            await session.execute(delete(CompanySubscription).where(CompanySubscription.company_id.in_(company_ids)))
            await session.execute(delete(CompanySubscription).where(CompanySubscription.plan_id.in_(plan_ids)))
            await session.execute(delete(Plan).where(Plan.code.like("test-admin-service-%")))
            await session.execute(delete(Compania).where(Compania.documento == TEST_COMPANY_DOCUMENT))
            await session.execute(delete(TipoDocumento).where(TipoDocumento.id == TEST_DOCUMENT_TYPE_ID))
            await session.commit()


def _payload(**overrides) -> PlanCreate:
    data = {
        "code": f"test-admin-service-{uuid.uuid4()}",
        "name": f"Test Admin Service {uuid.uuid4()}",
        "description": "Plan administrativo",
        "is_public": True,
        "is_active": True,
        "limits": {
            "admins": 1,
            "supervisors": 2,
            "technicians": 5,
            "projects": 10,
            "clients": 25,
            "units": 100,
            "work_orders_per_month": 300,
            "pdf_reports_per_month": 300,
            "storage_mb": 1024,
        },
        "features": {
            "offline_mode": True,
            "custom_checklists": False,
            "advanced_dashboard": False,
            "evidence_editing": True,
        },
    }
    data.update(overrides)
    return PlanCreate(**data)


async def _create_plan(session: AsyncSession, **overrides) -> Plan:
    data = {
        "code": f"test-admin-service-{uuid.uuid4()}",
        "name": f"Test Admin Service Existing {uuid.uuid4()}",
        "max_admins": 1,
        "max_supervisors": 2,
        "max_technicians": 5,
        "max_units": 100,
        "allow_offline_mode": True,
        "allow_custom_checklists": False,
        "allow_advanced_dashboard": False,
        "allow_evidence_editing": True,
        "is_active": True,
        "is_public": True,
    }
    data.update(overrides)
    plan = Plan(**data)
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan


async def _create_company(session: AsyncSession) -> Compania:
    document_type = await session.get(TipoDocumento, TEST_DOCUMENT_TYPE_ID)
    if document_type is None:
        document_type = TipoDocumento(
            id=TEST_DOCUMENT_TYPE_ID,
            nombre="Documento Plan Admin Service",
            descripcion="Fixture temporal para admin de planes",
        )
        session.add(document_type)
        await session.commit()

    company = Compania(
        id=uuid.uuid4(),
        nombre="Compania Plan Admin Service",
        documento=TEST_COMPANY_DOCUMENT,
        tipo_documento_id=TEST_DOCUMENT_TYPE_ID,
        email="plan-admin-service@test.local",
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
async def test_create_plan_successfully(db_session: AsyncSession):
    response = await PlanAdminService(db_session).create_plan(_payload(code=" TEST-ADMIN-SERVICE-CREATED "))

    assert response.code == "test-admin-service-created"
    assert response.limits.technicians == 5
    assert response.features.offline_mode is True


@pytest.mark.asyncio
async def test_create_plan_with_duplicate_code_fails(db_session: AsyncSession):
    await PlanAdminService(db_session).create_plan(_payload(code="test-admin-service-duplicate"))

    with pytest.raises(PlanCodeAlreadyExistsError):
        await PlanAdminService(db_session).create_plan(_payload(code="test-admin-service-duplicate"))


@pytest.mark.asyncio
async def test_create_plan_with_negative_limit_fails(db_session: AsyncSession):
    with pytest.raises(InvalidPlanPayloadError):
        await PlanAdminService(db_session).create_plan(
            _payload(limits={"technicians": -1})
        )


@pytest.mark.asyncio
async def test_create_plan_with_null_limits_works(db_session: AsyncSession):
    response = await PlanAdminService(db_session).create_plan(
        _payload(limits={"technicians": None, "units": None})
    )

    assert response.limits.technicians is None
    assert response.limits.units is None


@pytest.mark.asyncio
async def test_get_existing_plan_works(db_session: AsyncSession):
    plan = await _create_plan(db_session)

    response = await PlanAdminService(db_session).get_plan(plan.id)

    assert response.id == plan.id
    assert response.code == plan.code


@pytest.mark.asyncio
async def test_get_missing_plan_fails_with_controlled_error(db_session: AsyncSession):
    with pytest.raises(PlanNotFoundError):
        await PlanAdminService(db_session).get_plan(uuid.uuid4())


@pytest.mark.asyncio
async def test_update_name_and_description_works(db_session: AsyncSession):
    plan = await _create_plan(db_session)

    response = await PlanAdminService(db_session).update_plan(
        plan.id,
        PlanUpdate(name="Plan actualizado", description="Nuevo texto"),
    )

    assert response.name == "Plan actualizado"
    assert response.description == "Nuevo texto"


@pytest.mark.asyncio
async def test_update_partial_limits_preserves_unsent_limits(db_session: AsyncSession):
    plan = await _create_plan(db_session, max_technicians=5, max_units=100)

    response = await PlanAdminService(db_session).update_plan(
        plan.id,
        PlanUpdate(limits={"technicians": 10}),
    )

    assert response.limits.technicians == 10
    assert response.limits.units == 100


@pytest.mark.asyncio
async def test_update_partial_features_preserves_unsent_features(db_session: AsyncSession):
    plan = await _create_plan(
        db_session,
        allow_advanced_dashboard=False,
        allow_evidence_editing=True,
    )

    response = await PlanAdminService(db_session).update_plan(
        plan.id,
        PlanUpdate(features={"advanced_dashboard": True}),
    )

    assert response.features.advanced_dashboard is True
    assert response.features.evidence_editing is True


@pytest.mark.asyncio
async def test_update_code_to_duplicate_fails(db_session: AsyncSession):
    duplicate = await _create_plan(db_session, code="test-admin-service-code-a")
    plan = await _create_plan(db_session)

    with pytest.raises(PlanCodeAlreadyExistsError):
        await PlanAdminService(db_session).update_plan(plan.id, PlanUpdate(code=duplicate.code))


@pytest.mark.asyncio
async def test_deactivate_plan_without_active_subscriptions_works(db_session: AsyncSession):
    plan = await _create_plan(db_session)

    response = await PlanAdminService(db_session).deactivate_plan(plan.id)

    assert response.is_active is False


@pytest.mark.asyncio
async def test_deactivate_free_plan_fails(db_session: AsyncSession):
    service = PlanAdminService(db_session)
    free = (await db_session.execute(select(Plan).where(Plan.code == "free"))).scalars().first()
    if free is None:
        free = Plan(code="free", name=f"Free {uuid.uuid4()}", is_active=True, is_public=True)
        db_session.add(free)
        await db_session.commit()
        await db_session.refresh(free)

    with pytest.raises(FreePlanCannotBeDeactivatedError):
        await service.deactivate_plan(free.id)


@pytest.mark.asyncio
async def test_deactivate_plan_with_active_subscriptions_fails(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session)
    subscription = CompanySubscription(
        company_id=company.id,
        plan_id=plan.id,
        status="active",
        billing_period="monthly",
        start_date=date.today(),
    )
    db_session.add(subscription)
    await db_session.commit()

    with pytest.raises(PlanHasActiveSubscriptionsError):
        await PlanAdminService(db_session).deactivate_plan(plan.id)
