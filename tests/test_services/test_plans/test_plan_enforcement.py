import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Cliente,
    Compania,
    CompanySubscription,
    CompanyUsage,
    Plan,
    Proyecto,
    TipoDocumento,
    TipoUnidad,
    Unidad,
    Usuario,
)
from app.db.models.usuarios import Rol
from app.db.session import AsyncSessionLocal
from app.services.plans.enforcement_service import (
    NO_ACTIVE_SUBSCRIPTION_CODE,
    PlanEnforcementService,
)
from app.services.plans.constants import PLAN_LIMIT_REACHED_CODE
from app.services.plans.usage_service import CompanyUsageService


TEST_DOCUMENT_TYPE_ID = 996
TEST_UNIT_TYPE_ID = 996
TEST_COMPANY_DOCUMENT_PREFIX = "PLAN-ENFORCEMENT-"


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
            await session.execute(delete(Unidad).where(Unidad.company_id.in_(company_ids)))
            await session.execute(delete(Proyecto).where(Proyecto.company_id.in_(company_ids)))
            await session.execute(delete(Cliente).where(Cliente.compania_id.in_(company_ids)))
            await session.execute(delete(Usuario).where(Usuario.company_id.in_(company_ids)))
            await session.execute(delete(CompanySubscription).where(CompanySubscription.company_id.in_(company_ids)))
            await session.execute(delete(CompanyUsage).where(CompanyUsage.company_id.in_(company_ids)))
            await session.execute(delete(Plan).where(Plan.code.like("test-slice4-%")))
            await session.execute(delete(Compania).where(Compania.id.in_(company_ids)))
            await session.execute(delete(TipoUnidad).where(TipoUnidad.id == TEST_UNIT_TYPE_ID))
            await session.execute(delete(TipoDocumento).where(TipoDocumento.id == TEST_DOCUMENT_TYPE_ID))
            await session.commit()


async def _ensure_catalogs(session: AsyncSession) -> None:
    if await session.get(TipoDocumento, TEST_DOCUMENT_TYPE_ID) is None:
        session.add(
            TipoDocumento(
                id=TEST_DOCUMENT_TYPE_ID,
                nombre="Documento Test Enforcement",
                descripcion="Fixture temporal para enforcement de planes",
            )
        )
    if await session.get(TipoUnidad, TEST_UNIT_TYPE_ID) is None:
        session.add(TipoUnidad(id=TEST_UNIT_TYPE_ID, nombre="Tipo Unidad Test Enforcement"))
    await session.commit()


async def _create_company(session: AsyncSession) -> Compania:
    await _ensure_catalogs(session)
    company = Compania(
        id=uuid.uuid4(),
        nombre="Compania Enforcement",
        documento=f"{TEST_COMPANY_DOCUMENT_PREFIX}{uuid.uuid4()}",
        tipo_documento_id=TEST_DOCUMENT_TYPE_ID,
        email="enforcement@test.local",
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
        "code": f"test-slice4-{uuid.uuid4()}",
        "name": f"Test Slice 4 Plan {uuid.uuid4()}",
        "max_admins": None,
        "max_supervisors": None,
        "max_technicians": None,
        "max_clients": None,
        "max_projects": None,
        "max_units": None,
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


async def _create_user(session: AsyncSession, company_id, role: Rol, *, active: bool = True) -> Usuario:
    user_id = uuid.uuid4()
    user = Usuario(
        id=user_id,
        uid=f"slice4-{user_id}",
        display_name="Usuario Enforcement",
        company_id=company_id,
        document_id=f"DOC-{user_id}",
        document_type_id=TEST_DOCUMENT_TYPE_ID,
        email=f"slice4-{user_id}@test.local",
        phone_number="0000000",
        rol=role,
        is_active=active,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def _create_client(session: AsyncSession, company_id) -> Cliente:
    client = Cliente(
        id=uuid.uuid4(),
        nombre="Cliente Enforcement",
        documento=f"CLI-{uuid.uuid4()}",
        email="cliente-enforcement@test.local",
        telefono="0000000",
        ciudad="Test City",
        direccion="Test Address",
        tipo_documento_id=TEST_DOCUMENT_TYPE_ID,
        compania_id=company_id,
    )
    session.add(client)
    await session.commit()
    await session.refresh(client)
    return client


async def _create_project(session: AsyncSession, company_id, client_id=None) -> Proyecto:
    project = Proyecto(
        id=uuid.uuid4(),
        nombre="Proyecto Enforcement",
        direccion="Test Address",
        company_id=company_id,
        cliente_id=client_id,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def _create_unit(session: AsyncSession, company_id, project_id, client_id) -> Unidad:
    unit = Unidad(
        id=uuid.uuid4(),
        nombre=f"Unidad Enforcement {uuid.uuid4()}",
        proyecto_id=project_id,
        tipo_unidad_id=TEST_UNIT_TYPE_ID,
        company_id=company_id,
        cliente_id=client_id,
    )
    session.add(unit)
    await session.commit()
    await session.refresh(unit)
    return unit


def _assert_limit_error(exc: HTTPException, resource: str, current_usage: int, plan_limit: int) -> None:
    assert exc.status_code == 409
    assert exc.detail["code"] == PLAN_LIMIT_REACHED_CODE
    assert exc.detail["resource"] == resource
    assert exc.detail["current_usage"] == current_usage
    assert exc.detail["plan_limit"] == plan_limit


@pytest.mark.asyncio
async def test_allows_create_technician_below_limit(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_technicians=2)
    await _subscribe(db_session, company, plan)
    await _create_user(db_session, company.id, Rol.TECHNICIAN)

    await PlanEnforcementService(db_session).assert_can_create_user(company.id, Rol.TECHNICIAN)


@pytest.mark.asyncio
async def test_blocks_create_technician_at_limit(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_technicians=1)
    await _subscribe(db_session, company, plan)
    await _create_user(db_session, company.id, Rol.TECHNICIAN)

    with pytest.raises(HTTPException) as exc_info:
        await PlanEnforcementService(db_session).assert_can_create_user(company.id, Rol.TECHNICIAN)

    _assert_limit_error(exc_info.value, "technicians", 1, 1)


@pytest.mark.asyncio
async def test_blocks_create_supervisor_at_limit(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_supervisors=1)
    await _subscribe(db_session, company, plan)
    await _create_user(db_session, company.id, Rol.SUPERVISOR)

    with pytest.raises(HTTPException) as exc_info:
        await PlanEnforcementService(db_session).assert_can_create_user(company.id, Rol.SUPERVISOR)

    _assert_limit_error(exc_info.value, "supervisors", 1, 1)


@pytest.mark.asyncio
async def test_blocks_create_admin_at_limit(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_admins=1)
    await _subscribe(db_session, company, plan)
    await _create_user(db_session, company.id, Rol.ADMIN)

    with pytest.raises(HTTPException) as exc_info:
        await PlanEnforcementService(db_session).assert_can_create_user(company.id, Rol.ADMIN)

    _assert_limit_error(exc_info.value, "admins", 1, 1)


@pytest.mark.asyncio
async def test_allows_create_client_below_limit(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_clients=2)
    await _subscribe(db_session, company, plan)
    await _create_client(db_session, company.id)

    await PlanEnforcementService(db_session).assert_can_create_client(company.id)


@pytest.mark.asyncio
async def test_blocks_create_client_at_limit(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_clients=1)
    await _subscribe(db_session, company, plan)
    await _create_client(db_session, company.id)

    with pytest.raises(HTTPException) as exc_info:
        await PlanEnforcementService(db_session).assert_can_create_client(company.id)

    _assert_limit_error(exc_info.value, "clients", 1, 1)


@pytest.mark.asyncio
async def test_allows_create_project_below_limit(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_projects=2)
    await _subscribe(db_session, company, plan)
    client = await _create_client(db_session, company.id)
    await _create_project(db_session, company.id, client.id)

    await PlanEnforcementService(db_session).assert_can_create_project(company.id)


@pytest.mark.asyncio
async def test_blocks_create_project_at_limit(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_projects=1)
    await _subscribe(db_session, company, plan)
    client = await _create_client(db_session, company.id)
    await _create_project(db_session, company.id, client.id)

    with pytest.raises(HTTPException) as exc_info:
        await PlanEnforcementService(db_session).assert_can_create_project(company.id)

    _assert_limit_error(exc_info.value, "projects", 1, 1)


@pytest.mark.asyncio
async def test_allows_create_unit_below_limit(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_units=2)
    await _subscribe(db_session, company, plan)
    client = await _create_client(db_session, company.id)
    project = await _create_project(db_session, company.id, client.id)
    await _create_unit(db_session, company.id, project.id, client.id)

    await PlanEnforcementService(db_session).assert_can_create_unit(company.id)


@pytest.mark.asyncio
async def test_blocks_create_unit_at_limit(db_session: AsyncSession):
    company = await _create_company(db_session)
    plan = await _create_plan(db_session, max_units=1)
    await _subscribe(db_session, company, plan)
    client = await _create_client(db_session, company.id)
    project = await _create_project(db_session, company.id, client.id)
    await _create_unit(db_session, company.id, project.id, client.id)

    with pytest.raises(HTTPException) as exc_info:
        await PlanEnforcementService(db_session).assert_can_create_unit(company.id)

    _assert_limit_error(exc_info.value, "units", 1, 1)


@pytest.mark.asyncio
async def test_creation_fails_controlled_without_active_subscription(db_session: AsyncSession):
    company = await _create_company(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await PlanEnforcementService(db_session).assert_can_create_client(company.id)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == NO_ACTIVE_SUBSCRIPTION_CODE
    assert exc_info.value.detail["resource"] == "clients"


@pytest.mark.asyncio
async def test_refresh_company_usage_snapshot_uses_real_database_counts(db_session: AsyncSession):
    company = await _create_company(db_session)
    await _create_user(db_session, company.id, Rol.ADMIN)
    await _create_user(db_session, company.id, Rol.SUPERVISOR)
    await _create_user(db_session, company.id, Rol.TECHNICIAN)
    client = await _create_client(db_session, company.id)
    project = await _create_project(db_session, company.id, client.id)
    await _create_unit(db_session, company.id, project.id, client.id)

    usage = await CompanyUsageService(db_session).refresh_company_usage_snapshot(company.id, 2026, 5)

    assert usage.users_count == 3
    assert usage.admins_count == 1
    assert usage.supervisors_count == 1
    assert usage.technicians_count == 1
    assert usage.clients_count == 1
    assert usage.projects_count == 1
    assert usage.units_count == 1
