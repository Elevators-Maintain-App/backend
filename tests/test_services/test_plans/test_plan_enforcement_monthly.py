import uuid
from datetime import date, datetime, timedelta

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Cliente,
    Compania,
    CompanySubscription,
    CompanyUsage,
    OrdenDeTrabajo,
    PdfReportGenerationEvent,
    Plan,
    Prioridad,
    Proyecto,
    TipoDocumento,
    TipoOrden,
    TipoUnidad,
    Unidad,
)
from app.db.models.enums.estados_orden import EstadoOrden
from app.db.session import AsyncSessionLocal
from app.services.plans.constants import PLAN_LIMIT_REACHED_CODE
from app.services.plans.enforcement_service import (
    NO_ACTIVE_SUBSCRIPTION_CODE,
    PlanEnforcementService,
)
from app.services.plans.usage_service import CompanyUsageService


TEST_DOCUMENT_TYPE_ID = 997
TEST_UNIT_TYPE_ID = 997
TEST_ORDER_TYPE_ID = 997
TEST_ORDER_STATUS_ID = 997
TEST_PRIORITY_ID = 997
TEST_COMPANY_DOCUMENT_PREFIX = "PLAN-MONTHLY-ENFORCEMENT-"


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            company_ids = select(Compania.id).where(
                Compania.documento.like(f"{TEST_COMPANY_DOCUMENT_PREFIX}%")
            )
            await session.execute(delete(PdfReportGenerationEvent).where(PdfReportGenerationEvent.company_id.in_(company_ids)))
            await session.execute(delete(OrdenDeTrabajo).where(OrdenDeTrabajo.company_id.in_(company_ids)))
            await session.execute(delete(Unidad).where(Unidad.company_id.in_(company_ids)))
            await session.execute(delete(Proyecto).where(Proyecto.company_id.in_(company_ids)))
            await session.execute(delete(Cliente).where(Cliente.compania_id.in_(company_ids)))
            await session.execute(delete(CompanySubscription).where(CompanySubscription.company_id.in_(company_ids)))
            await session.execute(delete(CompanyUsage).where(CompanyUsage.company_id.in_(company_ids)))
            await session.execute(delete(Plan).where(Plan.code.like("test-slice5-%")))
            await session.execute(delete(Compania).where(Compania.id.in_(company_ids)))
            await session.execute(delete(TipoUnidad).where(TipoUnidad.id == TEST_UNIT_TYPE_ID))
            await session.execute(delete(TipoOrden).where(TipoOrden.id == TEST_ORDER_TYPE_ID))
            await session.execute(delete(EstadoOrden).where(EstadoOrden.id == TEST_ORDER_STATUS_ID))
            await session.execute(delete(Prioridad).where(Prioridad.id == TEST_PRIORITY_ID))
            await session.execute(delete(TipoDocumento).where(TipoDocumento.id == TEST_DOCUMENT_TYPE_ID))
            await session.commit()


async def _ensure_catalogs(session: AsyncSession) -> None:
    if await session.get(TipoDocumento, TEST_DOCUMENT_TYPE_ID) is None:
        session.add(TipoDocumento(id=TEST_DOCUMENT_TYPE_ID, nombre="Documento Test Monthly"))
    if await session.get(TipoUnidad, TEST_UNIT_TYPE_ID) is None:
        session.add(TipoUnidad(id=TEST_UNIT_TYPE_ID, nombre="Tipo Unidad Test Monthly"))
    if await session.get(TipoOrden, TEST_ORDER_TYPE_ID) is None:
        session.add(TipoOrden(id=TEST_ORDER_TYPE_ID, nombre="Tipo Orden Test Monthly"))
    if await session.get(EstadoOrden, TEST_ORDER_STATUS_ID) is None:
        session.add(EstadoOrden(id=TEST_ORDER_STATUS_ID, nombre="Estado Test Monthly"))
    if await session.get(Prioridad, TEST_PRIORITY_ID) is None:
        session.add(Prioridad(id=TEST_PRIORITY_ID, nombre="Prioridad Test Monthly"))
    await session.commit()


async def _create_company(session: AsyncSession) -> Compania:
    await _ensure_catalogs(session)
    company = Compania(
        id=uuid.uuid4(),
        nombre="Compania Monthly Enforcement",
        documento=f"{TEST_COMPANY_DOCUMENT_PREFIX}{uuid.uuid4()}",
        tipo_documento_id=TEST_DOCUMENT_TYPE_ID,
        email="monthly-enforcement@test.local",
        telefono="0000000",
        ciudad="Test City",
        direccion="Test Address",
    )
    session.add(company)
    await session.commit()
    await session.refresh(company)
    return company


async def _create_plan(session: AsyncSession, **overrides) -> Plan:
    plan_data = {
        "code": f"test-slice5-{uuid.uuid4()}",
        "name": f"Test Slice 5 Plan {uuid.uuid4()}",
        "max_work_orders_per_month": None,
        "max_pdf_reports_per_month": None,
        "is_active": True,
        "is_public": False,
    }
    plan_data.update(overrides)
    plan = Plan(**plan_data)
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan


async def _subscribe(session: AsyncSession, company: Compania, plan: Plan) -> CompanySubscription:
    subscription = CompanySubscription(
        company_id=company.id,
        plan_id=plan.id,
        status="active",
        billing_period="monthly",
        start_date=date.today() - timedelta(days=1),
        end_date=None,
    )
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription)
    return subscription


async def _create_client_project_unit(session: AsyncSession, company_id):
    client = Cliente(
        id=uuid.uuid4(),
        nombre="Cliente Monthly",
        documento=f"CLI-{uuid.uuid4()}",
        email="monthly-client@test.local",
        telefono="0000000",
        ciudad="Test City",
        direccion="Test Address",
        tipo_documento_id=TEST_DOCUMENT_TYPE_ID,
        compania_id=company_id,
    )
    session.add(client)
    await session.commit()
    await session.refresh(client)

    project = Proyecto(
        id=uuid.uuid4(),
        nombre="Proyecto Monthly",
        direccion="Test Address",
        company_id=company_id,
        cliente_id=client.id,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)

    unit = Unidad(
        id=uuid.uuid4(),
        nombre=f"Unidad Monthly {uuid.uuid4()}",
        proyecto_id=project.id,
        tipo_unidad_id=TEST_UNIT_TYPE_ID,
        company_id=company_id,
        cliente_id=client.id,
    )
    session.add(unit)
    await session.commit()
    await session.refresh(unit)
    return client, project, unit


async def _create_work_order(session: AsyncSession, company_id, unit: Unidad, created_at: datetime) -> OrdenDeTrabajo:
    order = OrdenDeTrabajo(
        id=uuid.uuid4(),
        referencia=f"TEST-{uuid.uuid4()}",
        descripcion="Orden Monthly",
        fecha=created_at.date(),
        tipo_orden_id=TEST_ORDER_TYPE_ID,
        estado_id=TEST_ORDER_STATUS_ID,
        prioridad_id=TEST_PRIORITY_ID,
        company_id=company_id,
        cliente_id=unit.cliente_id,
        supervisor_id="supervisor-test",
        tecnico_id="technician-test",
        unidad_id=unit.id,
        created_at=created_at,
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


async def _create_pdf_event(session: AsyncSession, company_id, created_at: datetime) -> PdfReportGenerationEvent:
    event = PdfReportGenerationEvent(
        company_id=company_id,
        report_type="final",
        storage_url="https://storage.example/report.pdf",
        status="success",
        created_at=created_at,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


def _this_month() -> tuple[datetime, datetime]:
    now = datetime.utcnow()
    current = datetime(now.year, now.month, 3, 12, 0, 0)
    previous_month_year = now.year if now.month > 1 else now.year - 1
    previous_month = now.month - 1 if now.month > 1 else 12
    previous = datetime(previous_month_year, previous_month, 3, 12, 0, 0)
    return current, previous


def _assert_limit_error(exc: HTTPException, resource: str, current_usage: int, plan_limit: int) -> None:
    assert exc.status_code == 409
    assert exc.detail["code"] == PLAN_LIMIT_REACHED_CODE
    assert exc.detail["resource"] == resource
    assert exc.detail["current_usage"] == current_usage
    assert exc.detail["plan_limit"] == plan_limit


async def _simulate_pdf_generation(
    db: AsyncSession,
    company_id,
    *,
    fail: bool = False,
) -> None:
    service = PlanEnforcementService(db)
    await service.assert_can_generate_pdf_report(company_id)
    if fail:
        raise RuntimeError("PDF generation failed")
    await service.record_successful_pdf_generation(
        company_id=company_id,
        orden_id=None,
        checklist_id=None,
        report_type="final",
        storage_url="https://storage.example/generated.pdf",
    )


@pytest.mark.asyncio
async def test_allows_create_work_order_below_monthly_limit(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_work_orders_per_month=2)
    await _subscribe(db_session, company, plan)
    _, _, unit = await _create_client_project_unit(db_session, company.id)
    current, _ = _this_month()
    await _create_work_order(db_session, company.id, unit, current)

    await PlanEnforcementService(db_session).assert_can_create_work_order(company.id)


@pytest.mark.asyncio
async def test_blocks_create_work_order_at_monthly_limit(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_work_orders_per_month=1)
    await _subscribe(db_session, company, plan)
    _, _, unit = await _create_client_project_unit(db_session, company.id)
    current, _ = _this_month()
    await _create_work_order(db_session, company.id, unit, current)

    with pytest.raises(HTTPException) as exc_info:
        await PlanEnforcementService(db_session).assert_can_create_work_order(company.id)

    _assert_limit_error(exc_info.value, "work_orders_per_month", 1, 1)


@pytest.mark.asyncio
async def test_work_order_monthly_count_ignores_previous_month(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_work_orders_per_month=1)
    await _subscribe(db_session, company, plan)
    _, _, unit = await _create_client_project_unit(db_session, company.id)
    _, previous = _this_month()
    await _create_work_order(db_session, company.id, unit, previous)

    await PlanEnforcementService(db_session).assert_can_create_work_order(company.id)


@pytest.mark.asyncio
async def test_create_work_order_fails_controlled_without_active_subscription(db_session: AsyncSession):
    company = await _create_company(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await PlanEnforcementService(db_session).assert_can_create_work_order(company.id)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == NO_ACTIVE_SUBSCRIPTION_CODE
    assert exc_info.value.detail["resource"] == "work_orders_per_month"


@pytest.mark.asyncio
async def test_allows_generate_pdf_below_monthly_limit(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_pdf_reports_per_month=2)
    await _subscribe(db_session, company, plan)
    current, _ = _this_month()
    await _create_pdf_event(db_session, company.id, current)

    await PlanEnforcementService(db_session).assert_can_generate_pdf_report(company.id)


@pytest.mark.asyncio
async def test_blocks_generate_pdf_at_monthly_limit(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_pdf_reports_per_month=1)
    await _subscribe(db_session, company, plan)
    current, _ = _this_month()
    await _create_pdf_event(db_session, company.id, current)

    with pytest.raises(HTTPException) as exc_info:
        await PlanEnforcementService(db_session).assert_can_generate_pdf_report(company.id)

    _assert_limit_error(exc_info.value, "pdf_reports_per_month", 1, 1)


@pytest.mark.asyncio
async def test_pdf_monthly_count_ignores_previous_month(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_pdf_reports_per_month=1)
    await _subscribe(db_session, company, plan)
    _, previous = _this_month()
    await _create_pdf_event(db_session, company.id, previous)

    await PlanEnforcementService(db_session).assert_can_generate_pdf_report(company.id)


@pytest.mark.asyncio
async def test_failed_pdf_generation_does_not_increment_consumption(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_pdf_reports_per_month=1)
    await _subscribe(db_session, company, plan)

    with pytest.raises(RuntimeError):
        await _simulate_pdf_generation(db_session, company.id, fail=True)

    count = (
        await db_session.execute(
            select(func.count())
            .select_from(PdfReportGenerationEvent)
            .where(PdfReportGenerationEvent.company_id == company.id)
        )
    ).scalar_one()
    assert count == 0


@pytest.mark.asyncio
async def test_reading_existing_pdf_url_does_not_increment_consumption(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_pdf_reports_per_month=2)
    await _subscribe(db_session, company, plan)
    current, _ = _this_month()
    await _create_pdf_event(db_session, company.id, current)

    before = await PlanEnforcementService(db_session).count_current_usage(company.id, "pdf_reports_per_month")
    existing_url = "https://storage.example/existing.pdf"
    after = await PlanEnforcementService(db_session).count_current_usage(company.id, "pdf_reports_per_month")

    assert existing_url
    assert before == 1
    assert after == 1


@pytest.mark.asyncio
async def test_monthly_usage_snapshot_includes_work_orders_and_pdf_reports(db_session: AsyncSession):
    company = await _create_company(db_session)
    _, _, unit = await _create_client_project_unit(db_session, company.id)
    current, _ = _this_month()
    await _create_work_order(db_session, company.id, unit, current)
    await _create_pdf_event(db_session, company.id, current)

    usage = await CompanyUsageService(db_session).refresh_company_usage_snapshot(
        company.id,
        current.year,
        current.month,
    )

    assert usage.work_orders_created == 1
    assert usage.pdf_reports_generated == 1
