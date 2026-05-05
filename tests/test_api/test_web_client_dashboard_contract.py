from __future__ import annotations

from datetime import date, datetime, timezone
from importlib import import_module
from types import SimpleNamespace
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql

from app.auth.firebase import get_current_firebase_user
from app.auth import firebase as firebase_auth_module
from app.db.models.usuarios import Rol
from app.db.session import get_db
from app.middleware.observability import observability_middleware
from app.services.web.client_portal_service import WebClientPortalService


web_client = import_module("app.api.routes.web_client")


COMPANY_ID = UUID("33333333-3333-3333-3333-333333333333")
CLIENT_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_CLIENT_ORDER_ID = UUID("99999999-9999-9999-9999-999999999999")
VISIBLE_ORDER_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
VISIBLE_UNIT_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
OTHER_CLIENT_UNIT_ID = UUID("88888888-8888-8888-8888-888888888888")
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


class FakeWebClientPortalService:
    calls = []

    def __init__(self, db):
        self.db = db

    def _ensure_client_id(self, current_user):
        if not current_user.client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El usuario cliente no tiene client_id asociado",
            )

    async def get_units(self, current_user, *, page, page_size, search=None, project_id=None):
        self._ensure_client_id(current_user)
        self.calls.append(("units", {"client_id": current_user.client_id, "page": page}))
        return {
            "data": [
                {
                    "id": VISIBLE_UNIT_ID,
                    "name": "Unidad visible",
                    "project_id": UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
                    "project": "Proyecto visible",
                    "type": "Ascensor",
                    "kpi_functioning": "98%",
                }
            ],
            "total": 1,
            "page": page,
            "page_size": page_size,
            "total_pages": 1,
        }

    async def get_unit_detail(self, current_user, unit_id):
        self._ensure_client_id(current_user)
        if unit_id == OTHER_CLIENT_UNIT_ID:
            raise HTTPException(status_code=404, detail="Unidad no encontrada")
        return {
            "id": unit_id,
            "name": "Unidad visible",
            "project_id": UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
            "project": "Proyecto visible",
            "type": "Ascensor",
            "kpi_functioning": "98%",
            "company_id": COMPANY_ID,
            "client_id": current_user.client_id,
            "created_at": NOW,
            "updated_at": NOW,
        }

    async def get_orders(
        self,
        current_user,
        *,
        page,
        page_size,
        search=None,
        status_name=None,
        unit_id=None,
        project_id=None,
    ):
        self._ensure_client_id(current_user)
        self.calls.append(("orders", {"client_id": current_user.client_id, "page": page}))
        return {
            "data": [
                {
                    "id": VISIBLE_ORDER_ID,
                    "reference": "OT-001",
                    "date": date(2026, 1, 2),
                    "status": "Cerrada",
                    "project_id": UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
                    "project": "Proyecto visible",
                    "unit_id": VISIBLE_UNIT_ID,
                    "unit": "Unidad visible",
                    "type": "Mantenimiento",
                    "priority": "Alta",
                    "has_report": True,
                }
            ],
            "total": 1,
            "page": page,
            "page_size": page_size,
            "total_pages": 1,
        }

    async def get_order_detail(self, current_user, order_id):
        self._ensure_client_id(current_user)
        if order_id == OTHER_CLIENT_ORDER_ID:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        return {
            "id": order_id,
            "reference": "OT-001",
            "date": date(2026, 1, 2),
            "status": "Cerrada",
            "project_id": UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
            "project": "Proyecto visible",
            "unit_id": VISIBLE_UNIT_ID,
            "unit": "Unidad visible",
            "type": "Mantenimiento",
            "priority": "Alta",
            "has_report": True,
            "description": "Descripcion",
            "observations": "Observaciones",
            "technician": "Tecnico Uno",
            "supervisor": "Supervisor Uno",
            "final_report_url": "https://storage.example/reporte.pdf",
        }

    async def get_order_report(self, current_user, order_id):
        self._ensure_client_id(current_user)
        if order_id == UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"):
            raise HTTPException(
                status_code=403,
                detail="El reporte solo esta disponible para ordenes cerradas",
            )
        return {"report_url": "https://storage.example/reporte.pdf"}


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
    FakeWebClientPortalService.calls = []
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


def test_web_client_dashboard_uses_postgres_client_id_before_firestore(monkeypatch):
    FakeWebClientDashboardService.calls = []

    monkeypatch.setattr(
        web_client,
        "WebClientDashboardService",
        FakeWebClientDashboardService,
    )

    class FakeUsuarioCrud:
        async def get_usuario_con_relaciones(self, db, uid):
            return SimpleNamespace(
                uid=uid,
                display_name="Cliente PostgreSQL",
                email="cliente.pg@example.invalid",
                company_id=COMPANY_ID,
                company=SimpleNamespace(nombre="Compania PostgreSQL"),
                client_id=CLIENT_ID,
                client=SimpleNamespace(nombre="Cliente PostgreSQL"),
                document_id="DOC-PG",
                document_type_id=1,
                document_type=SimpleNamespace(nombre="Cedula"),
                photo_url=None,
                rol=Rol.CLIENT,
                created_at=NOW,
            )

    def fake_verify_id_token(token):
        assert token == "firebase-token"
        return {"uid": "client-from-postgres"}

    def fail_if_firestore_is_used():
        raise AssertionError("Firestore no debe ser fuente principal si existe PostgreSQL")

    monkeypatch.setattr(firebase_auth_module, "usuario_crud", FakeUsuarioCrud())
    monkeypatch.setattr(firebase_auth_module.firebase_auth, "verify_id_token", fake_verify_id_token)
    monkeypatch.setattr(firebase_auth_module, "get_firestore_client", fail_if_firestore_is_used)

    app = FastAPI()
    app.middleware("http")(observability_middleware)
    app.include_router(web_client.router, prefix="/api/web/client")

    async def fake_db():
        return DummyDB()

    app.dependency_overrides[get_db] = fake_db
    client = TestClient(app)

    response = client.get(
        "/api/web/client/dashboard",
        headers={
            "Authorization": "Bearer firebase-token",
            "X-Request-ID": "web-client-dashboard-postgres-auth",
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "web-client-dashboard-postgres-auth"
    assert FakeWebClientDashboardService.calls == [
        {
            "uid": "client-from-postgres",
            "client_id": CLIENT_ID,
            "company_id": COMPANY_ID,
        }
    ]


def test_web_client_units_do_not_return_other_client_data(monkeypatch):
    monkeypatch.setattr(web_client, "WebClientPortalService", FakeWebClientPortalService)
    client = TestClient(create_app(role="client"))

    response = client.get(
        "/api/web/client/units",
        headers={"X-Request-ID": "web-client-units"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "web-client-units"
    ids = {unit["id"] for unit in response.json()["data"]}
    assert str(VISIBLE_UNIT_ID) in ids
    assert str(OTHER_CLIENT_UNIT_ID) not in ids


def test_web_client_cannot_get_other_client_unit(monkeypatch):
    monkeypatch.setattr(web_client, "WebClientPortalService", FakeWebClientPortalService)
    client = TestClient(create_app(role="client"))

    response = client.get(
        f"/api/web/client/units/{OTHER_CLIENT_UNIT_ID}",
        headers={"X-Request-ID": "web-client-unit-other"},
    )

    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == "web-client-unit-other"


def test_web_client_orders_do_not_return_other_client_data(monkeypatch):
    monkeypatch.setattr(web_client, "WebClientPortalService", FakeWebClientPortalService)
    client = TestClient(create_app(role="client"))

    response = client.get(
        "/api/web/client/orders",
        headers={"X-Request-ID": "web-client-orders"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "web-client-orders"
    ids = {order["id"] for order in response.json()["data"]}
    assert str(VISIBLE_ORDER_ID) in ids
    assert str(OTHER_CLIENT_ORDER_ID) not in ids


def test_web_client_cannot_get_other_client_order(monkeypatch):
    monkeypatch.setattr(web_client, "WebClientPortalService", FakeWebClientPortalService)
    client = TestClient(create_app(role="client"))

    response = client.get(
        f"/api/web/client/orders/{OTHER_CLIENT_ORDER_ID}",
        headers={"X-Request-ID": "web-client-order-other"},
    )

    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == "web-client-order-other"


def test_web_client_closed_order_with_report_returns_report(monkeypatch):
    monkeypatch.setattr(web_client, "WebClientPortalService", FakeWebClientPortalService)
    client = TestClient(create_app(role="client"))

    response = client.get(
        f"/api/web/client/orders/{VISIBLE_ORDER_ID}/report",
        headers={"X-Request-ID": "web-client-order-report"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "web-client-order-report"
    assert response.json() == {"report_url": "https://storage.example/reporte.pdf"}


def test_web_client_open_order_does_not_allow_report(monkeypatch):
    monkeypatch.setattr(web_client, "WebClientPortalService", FakeWebClientPortalService)
    client = TestClient(create_app(role="client"))

    response = client.get(
        "/api/web/client/orders/dddddddd-dddd-dddd-dddd-dddddddddddd/report",
        headers={"X-Request-ID": "web-client-order-open-report"},
    )

    assert response.status_code == 403
    assert response.headers["X-Request-ID"] == "web-client-order-open-report"


def test_web_client_units_without_client_id_returns_clear_error(monkeypatch):
    monkeypatch.setattr(web_client, "WebClientPortalService", FakeWebClientPortalService)
    client = TestClient(create_app(role="client", client_id=None))

    response = client.get(
        "/api/web/client/units",
        headers={"X-Request-ID": "web-client-units-no-client-id"},
    )

    assert response.status_code == 403
    assert response.headers["X-Request-ID"] == "web-client-units-no-client-id"
    assert response.json()["detail"] == "El usuario cliente no tiene client_id asociado"


def test_web_client_portal_queries_do_not_filter_on_legacy_client_id_columns():
    service = WebClientPortalService(DummyDB())
    dialect = postgresql.dialect()

    unit_sql = str(
        service._unit_base_query(CLIENT_ID, COMPANY_ID).compile(
            dialect=dialect,
            compile_kwargs={"literal_binds": False},
        )
    )
    order_sql = str(
        service._order_base_query(CLIENT_ID, COMPANY_ID).compile(
            dialect=dialect,
            compile_kwargs={"literal_binds": False},
        )
    )

    assert "proyectos.cliente_id =" in unit_sql
    assert "proyectos.cliente_id =" in order_sql
    assert "unidades.cliente_id =" not in unit_sql
    assert "unidades.cliente_id =" not in order_sql
    assert "ordenes_de_trabajo.cliente_id =" not in order_sql
