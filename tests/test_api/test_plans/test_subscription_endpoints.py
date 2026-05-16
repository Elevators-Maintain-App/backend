from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from importlib import import_module
from types import SimpleNamespace
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi import FastAPI, Request
from httpx import AsyncClient
from sqlalchemy import delete, func, select

from app.auth.firebase import get_current_firebase_user
from app.db.models import Compania, CompanySubscription, CompanyUsage, Plan, TipoDocumento
from app.db.session import AsyncSessionLocal, get_db
from app.middleware.observability import observability_middleware


plans = import_module("app.api.routes.plans")
subscriptions = import_module("app.api.routes.subscriptions")


TEST_DOCUMENT_TYPE_ID = 993
COMPANY_ID = UUID("99999999-9999-9999-9999-999999999993")
OTHER_COMPANY_ID = UUID("99999999-9999-9999-9999-999999999994")
NOW = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)


def auth_user(role: str, company_id: UUID = COMPANY_ID):
    return SimpleNamespace(
        uid=f"{role}-subscription-user",
        rol=SimpleNamespace(value=role),
        role=role,
        company_id=company_id,
        created_time=NOW,
    )


def create_app(role: str = "admin", company_id: UUID = COMPANY_ID) -> FastAPI:
    app = FastAPI()
    app.middleware("http")(observability_middleware)
    app.include_router(plans.router, prefix="/api")
    app.include_router(subscriptions.router, prefix="/api")

    async def fake_db():
        async with AsyncSessionLocal() as session:
            yield session

    async def fake_auth_dependency(request: Request):
        user = auth_user(role, company_id)
        request.state.current_user = user
        return user

    app.dependency_overrides[get_db] = fake_db
    app.dependency_overrides[get_current_firebase_user] = fake_auth_dependency
    return app


async def cleanup_test_data():
    async with AsyncSessionLocal() as session:
        company_ids = [COMPANY_ID, OTHER_COMPANY_ID]
        await session.execute(delete(CompanySubscription).where(CompanySubscription.company_id.in_(company_ids)))
        await session.execute(delete(CompanyUsage).where(CompanyUsage.company_id.in_(company_ids)))
        await session.execute(delete(Plan).where(Plan.code.like("test-api-slice3-%")))
        await session.execute(delete(Compania).where(Compania.id.in_(company_ids)))
        await session.execute(delete(TipoDocumento).where(TipoDocumento.id == TEST_DOCUMENT_TYPE_ID))
        await session.commit()


async def seed_company_and_plan(*, with_subscription: bool = True, active_plan: bool = True):
    async with AsyncSessionLocal() as session:
        document_type = await session.get(TipoDocumento, TEST_DOCUMENT_TYPE_ID)
        if document_type is None:
            document_type = TipoDocumento(
                id=TEST_DOCUMENT_TYPE_ID,
                nombre="Documento Test API Planes",
                descripcion="Fixture temporal para API de planes",
            )
            session.add(document_type)

        company = Compania(
            id=COMPANY_ID,
            nombre="Compania API Planes",
            documento="PLANS-API-TEST-COMPANY",
            tipo_documento_id=TEST_DOCUMENT_TYPE_ID,
            email="plans-api@test.local",
            telefono="0000000",
            pais_id=None,
            ciudad="Test City",
            direccion="Test Address",
            logo=None,
        )
        other_company = Compania(
            id=OTHER_COMPANY_ID,
            nombre="Otra Compania API Planes",
            documento="PLANS-API-TEST-COMPANY-OTHER",
            tipo_documento_id=TEST_DOCUMENT_TYPE_ID,
            email="plans-api-other@test.local",
            telefono="0000000",
            pais_id=None,
            ciudad="Test City",
            direccion="Test Address",
            logo=None,
        )
        plan = Plan(
            id=uuid.uuid4(),
            code=f"test-api-slice3-{uuid.uuid4()}",
            name=f"Test API Slice 3 Plan {uuid.uuid4()}",
            description="Plan para contrato API",
            max_admins=2,
            max_supervisors=3,
            max_technicians=10,
            max_projects=10,
            max_clients=20,
            max_units=100,
            max_work_orders_per_month=300,
            max_pdf_reports_per_month=300,
            storage_limit_mb=1024,
            allow_offline_mode=True,
            allow_custom_checklists=True,
            allow_advanced_dashboard=True,
            allow_evidence_editing=False,
            is_public=True,
            is_active=active_plan,
        )
        session.add_all([company, other_company, plan])
        await session.flush()

        subscription = None
        if with_subscription:
            subscription = CompanySubscription(
                company_id=company.id,
                plan_id=plan.id,
                status="active",
                billing_period="monthly",
                start_date=date(2026, 5, 1),
                end_date=date(2026, 6, 1),
            )
            session.add(subscription)

        await session.commit()
        await session.refresh(plan)
        if subscription is not None:
            await session.refresh(subscription)

        return {"company": company, "other_company": other_company, "plan": plan, "subscription": subscription}


@pytest_asyncio.fixture(autouse=True)
async def clean_data():
    await cleanup_test_data()
    yield
    await cleanup_test_data()


@pytest.mark.asyncio
async def test_authenticated_user_can_get_subscription_me_with_usage_created():
    seeded = await seed_company_and_plan()
    async with AsyncClient(app=create_app(role="admin"), base_url="http://test") as client:
        response = await client.get("/api/subscription/me")

    assert response.status_code == 200
    payload = response.json()
    assert payload["company_id"] == str(COMPANY_ID)
    assert payload["subscription"]["status"] == "active"
    assert payload["plan"]["id"] == str(seeded["plan"].id)
    assert payload["limits"]["technicians"] == 10
    assert payload["limits"]["storage_mb"] == 1024
    assert payload["features"]["offline_mode"] is True
    assert payload["features"]["evidence_editing"] is False
    assert payload["usage"]["work_orders_created"] == 0
    assert payload["usage"]["pdf_reports_generated"] == 0

    async def usage_count():
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(func.count())
                .select_from(CompanyUsage)
                .where(CompanyUsage.company_id == COMPANY_ID)
            )
            return result.scalar_one()

    assert await usage_count() == 1


@pytest.mark.asyncio
async def test_subscription_me_returns_no_active_subscription_when_missing():
    await seed_company_and_plan(with_subscription=False)
    async with AsyncClient(app=create_app(role="admin"), base_url="http://test") as client:
        response = await client.get("/api/subscription/me")

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "NO_ACTIVE_SUBSCRIPTION"


@pytest.mark.asyncio
async def test_non_admin_cannot_access_admin_endpoints():
    async with AsyncClient(app=create_app(role="admin"), base_url="http://test") as client:
        response = await client.get("/api/admin/plans")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_superadmin_can_list_plans_and_include_inactive():
    active = (await seed_company_and_plan(active_plan=True))["plan"]

    async def add_inactive_plan():
        async with AsyncSessionLocal() as session:
            inactive = Plan(
                code=f"test-api-slice3-inactive-{uuid.uuid4()}",
                name=f"Test API Slice 3 Inactive {uuid.uuid4()}",
                is_active=False,
                is_public=False,
            )
            session.add(inactive)
            await session.commit()
            await session.refresh(inactive)
            return inactive

    inactive = await add_inactive_plan()
    async with AsyncClient(app=create_app(role="superAdmin"), base_url="http://test") as client:
        active_response = await client.get("/api/admin/plans")
        all_response = await client.get("/api/admin/plans", params={"include_inactive": "true"})

    assert active_response.status_code == 200
    assert str(active.id) in {item["id"] for item in active_response.json()}
    assert str(inactive.id) not in {item["id"] for item in active_response.json()}
    assert all_response.status_code == 200
    assert str(inactive.id) in {item["id"] for item in all_response.json()}


@pytest.mark.asyncio
async def test_superadmin_can_get_company_subscription():
    seeded = await seed_company_and_plan()
    async with AsyncClient(app=create_app(role="superAdmin"), base_url="http://test") as client:
        response = await client.get(f"/api/admin/companies/{COMPANY_ID}/subscription")

    assert response.status_code == 200
    assert response.json()["plan"]["id"] == str(seeded["plan"].id)


@pytest.mark.asyncio
async def test_superadmin_can_change_company_subscription_without_duplicate_active_subscriptions():
    seeded = await seed_company_and_plan()

    async def add_replacement_plan():
        async with AsyncSessionLocal() as session:
            plan = Plan(
                code=f"test-api-slice3-replacement-{uuid.uuid4()}",
                name=f"Test API Slice 3 Replacement {uuid.uuid4()}",
                max_technicians=50,
                allow_offline_mode=True,
                is_active=True,
                is_public=False,
            )
            session.add(plan)
            await session.commit()
            await session.refresh(plan)
            return plan

    replacement_plan = await add_replacement_plan()
    async with AsyncClient(app=create_app(role="superAdmin"), base_url="http://test") as client:
        response = await client.post(
            f"/api/admin/companies/{COMPANY_ID}/subscription",
            json={
                "plan_id": str(replacement_plan.id),
                "status": "active",
                "billing_period": "monthly",
                "start_date": "2026-05-15",
                "end_date": "2026-06-15",
            },
        )

    assert response.status_code == 201
    assert response.json()["plan"]["id"] == str(replacement_plan.id)

    async def active_subscription_count():
        async with AsyncSessionLocal() as session:
            rows = (
                await session.execute(
                    select(CompanySubscription).where(CompanySubscription.company_id == COMPANY_ID)
                )
            ).scalars().all()
            active_rows = [
                row for row in rows
                if row.status in {"active", "trial", "trialing"} and (row.end_date is None or row.end_date >= date.today())
            ]
            original = await session.get(CompanySubscription, seeded["subscription"].id)
            return len(active_rows), original.status

    count, original_status = await active_subscription_count()
    assert count == 1
    assert original_status == "cancelled"


@pytest.mark.asyncio
async def test_assign_subscription_rejects_inactive_plan():
    seeded = await seed_company_and_plan(active_plan=False)
    async with AsyncClient(app=create_app(role="superAdmin"), base_url="http://test") as client:
        response = await client.post(
            f"/api/admin/companies/{COMPANY_ID}/subscription",
            json={
                "plan_id": str(seeded["plan"].id),
                "status": "active",
                "billing_period": "monthly",
                "start_date": "2026-05-15",
                "end_date": "2026-06-15",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "PLAN_INACTIVE"
