from __future__ import annotations

from datetime import date, datetime, timezone
from importlib import import_module
from types import SimpleNamespace
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.testclient import TestClient

from app.auth.firebase import get_current_firebase_user
from app.db.session import get_db
from app.middleware.observability import observability_middleware


web_client = import_module("app.api.routes.web_client")


COMPANY_ID = UUID("33333333-3333-3333-3333-333333333333")
CLIENT_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_CLIENT_ORDER_ID = UUID("99999999-9999-9999-9999-999999999999")
VISIBLE_ORDER_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class DummyDB:
    pass


class FakeWebClientDashboardService:
    calls = []

    def __init__(self, db):
        self.db = db

    async def get_dashboard(self, current_user):
        self.calls.append(
            {
                "uid": current_user.uid,
                "client_id": current_user.client_id,
                "company_id": current_user.company_id,
            }
        )
        if not current_user.client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El usuario cliente no tiene client_id asociado",
            )
        return {
            "client": {
                "id": current_user.client_id,
                "name": "Cliente de Prueba 1",
            },
            "summary": {
                "total_projects": 2,
                "total_units": 3,
                "open_orders": 4,
                "closed_orders": 1,
            },
            "recent_orders": [
                {
                    "id": VISIBLE_ORDER_ID,
                    "reference": "OT-001",
                    "date": date(2026, 1, 2),
                    "status": "En ejecucion",
                    "unit": "Unidad visible",
                    "project": "Proyecto visible",
                }
            ],
        }


def auth_user(role: str, *, client_id=CLIENT_ID):
    return SimpleNamespace(
        uid="web-client-auth-user",
        rol=SimpleNamespace(value=role),
        role=role,
        company_id=COMPANY_ID,
        client_id=client_id,
        created_time=NOW,
    )


def create_app(role: str | None = "client", *, client_id=CLIENT_ID) -> FastAPI:
    FakeWebClientDashboardService.calls = []
    app = FastAPI()
    app.middleware("http")(observability_middleware)
    app.include_router(web_client.router, prefix="/api/web/client")

    async def fake_db():
        return DummyDB()

    async def fake_auth_dependency(request: Request):
        user = auth_user(role or "anonymous", client_id=client_id)
        request.state.current_user = user
        return user

    app.dependency_overrides[get_db] = fake_db
    if role is not None:
        app.dependency_overrides[get_current_firebase_user] = fake_auth_dependency

    return app


def test_web_client_dashboard_without_token_is_not_allowed_and_keeps_request_id(
    monkeypatch,
):
    monkeypatch.setattr(
        web_client,
        "WebClientDashboardService",
        FakeWebClientDashboardService,
    )
    client = TestClient(create_app(role=None))

    response = client.get(
        "/api/web/client/dashboard",
        headers={"X-Request-ID": "web-client-dashboard-no-token"},
    )

    assert response.status_code in {401, 403}
    assert response.headers["X-Request-ID"] == "web-client-dashboard-no-token"
    assert FakeWebClientDashboardService.calls == []


def test_web_client_dashboard_with_invalid_role_is_forbidden(monkeypatch):
    monkeypatch.setattr(
        web_client,
        "WebClientDashboardService",
        FakeWebClientDashboardService,
    )
    client = TestClient(create_app(role="admin"))

    response = client.get(
        "/api/web/client/dashboard",
        headers={"X-Request-ID": "web-client-dashboard-invalid-role"},
    )

    assert response.status_code == 403
    assert response.headers["X-Request-ID"] == "web-client-dashboard-invalid-role"
    assert FakeWebClientDashboardService.calls == []


def test_web_client_dashboard_without_client_id_returns_clear_error(monkeypatch):
    monkeypatch.setattr(
        web_client,
        "WebClientDashboardService",
        FakeWebClientDashboardService,
    )
    client = TestClient(create_app(role="client", client_id=None))

    response = client.get(
        "/api/web/client/dashboard",
        headers={"X-Request-ID": "web-client-dashboard-no-client-id"},
    )

    assert response.status_code == 403
    assert response.headers["X-Request-ID"] == "web-client-dashboard-no-client-id"
    assert response.json()["detail"] == "El usuario cliente no tiene client_id asociado"


def test_web_client_dashboard_with_client_role_returns_contract(monkeypatch):
    monkeypatch.setattr(
        web_client,
        "WebClientDashboardService",
        FakeWebClientDashboardService,
    )
    client = TestClient(create_app(role="client"))

    response = client.get(
        "/api/web/client/dashboard",
        headers={"X-Request-ID": "web-client-dashboard-allowed"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "web-client-dashboard-allowed"
    payload = response.json()
    assert set(payload.keys()) == {"client", "summary", "recent_orders"}
    assert payload["client"] == {
        "id": str(CLIENT_ID),
        "name": "Cliente de Prueba 1",
    }
    assert payload["summary"] == {
        "total_projects": 2,
        "total_units": 3,
        "open_orders": 4,
        "closed_orders": 1,
    }
    assert payload["recent_orders"] == [
        {
            "id": str(VISIBLE_ORDER_ID),
            "reference": "OT-001",
            "date": "2026-01-02",
            "status": "En ejecucion",
            "unit": "Unidad visible",
            "project": "Proyecto visible",
        }
    ]


def test_web_client_dashboard_does_not_return_other_client_data(monkeypatch):
    monkeypatch.setattr(
        web_client,
        "WebClientDashboardService",
        FakeWebClientDashboardService,
    )
    client = TestClient(create_app(role="client"))

    response = client.get(
        "/api/web/client/dashboard",
        headers={"X-Request-ID": "web-client-dashboard-tenant"},
    )

    assert response.status_code == 200
    order_ids = {order["id"] for order in response.json()["recent_orders"]}
    assert str(VISIBLE_ORDER_ID) in order_ids
    assert str(OTHER_CLIENT_ORDER_ID) not in order_ids
