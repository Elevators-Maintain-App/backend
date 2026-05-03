from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest
from importlib import import_module
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.auth.firebase import get_current_firebase_user
from app.db.session import get_db
from app.middleware.observability import observability_middleware

checklists = import_module("app.api.routes.checklists")
dashboard = import_module("app.api.routes.dashboard")
ordenes_de_trabajo = import_module("app.api.routes.ordenes_de_trabajo")
ordenes_seguimiento = import_module("app.api.routes.ordenes_seguimiento")


ORDER_ID = UUID("11111111-1111-1111-1111-111111111111")
CHECKLIST_ID = UUID("22222222-2222-2222-2222-222222222222")
COMPANY_ID = UUID("33333333-3333-3333-3333-333333333333")


class DummyDB:
    async def commit(self):
        return None


class FakeDashboardService:
    def __init__(self, db):
        self.db = db

    async def get_super_admin_dashboard(self, current_user):
        return {"usuarios": 0, "proyectos": 0, "planes": 0, "companias": 0}

    async def get_admin_dashboard(self, current_user):
        return {
            "clientes": 0,
            "proyectos": 0,
            "usuarios": 0,
            "ordenes_trabajo": 0,
            "unidades": 0,
        }


class FakeDashboardOrdenTrabajoService:
    def __init__(self, db):
        self.db = db

    async def get_dashboard_data(self, **kwargs):
        return {
            "ordenes_programadas": 0,
            "ordenes_completadas": 0,
            "ordenes_pendientes": 0,
            "cumplimiento_decimal": 0.0,
            "cumplimiento_label": "0%",
            "cumplimiento_str": "0%",
            "ordenes_en_curso": [],
        }

    async def get_dashboard_data_supervisor(self, **kwargs):
        return {
            "ordenes_programadas": 0,
            "ordenes_cerradas": 0,
            "ordenes_por_validar": 0,
            "ordenes_pendientes": 0,
            "ordenes_en_ejecucion": 0,
            "ordenes_atrasadas": 0,
            "cumplimiento_decimal": 0.0,
            "cumplimiento_label": "0%",
            "cumplimiento_str": "0%",
            "ordenes": [],
        }


class FakeOrdenDeTrabajoService:
    def __init__(self, db):
        self.db = db

    async def list_summary_by_company(self, company_id):
        return []

    async def list_ordenes_supervisor_filtradas(self, **kwargs):
        return []


class FakeChecklistService:
    def __init__(self, db):
        self.db = db

    async def init_checklist(self, orden_id):
        return None

    async def get_checklist(self, orden_id):
        return {
            "id": CHECKLIST_ID,
            "orden_trabajo_id": orden_id,
            "hora_entrada": None,
            "hora_salida": None,
            "observaciones": None,
            "firma_tecnico": None,
            "firma_cliente": None,
            "check_metadata": {},
            "items": [],
            "total_steps": 0,
            "step_numbers": [],
            "current_step": 0,
        }

    async def update_item(self, **kwargs):
        return {
            "evidencia_data": kwargs.get("evidencia_data"),
            "comentario": kwargs.get("comentario"),
            "confirm": kwargs.get("confirm"),
        }

    async def sync_full_checklist(self, orden_id, payload):
        return None


class FakeOrdenService:
    def __init__(self, db):
        self.db = db

    async def iniciar(self, orden, body):
        return None

    async def reanudar(self, orden, body):
        return None

    async def enviar_a_validacion(self, orden, body):
        return None

    async def finalizar(self, orden, body):
        return None

    async def obtener_datos_reporte_prerevision(self, orden_id):
        return {
            "url": "https://example.invalid/reporte.pdf",
            "proyecto": "Proyecto smoke",
            "unidad": "Unidad smoke",
            "estado": "En Validacion",
            "fecha": datetime(2026, 1, 1, tzinfo=timezone.utc),
        }


async def fake_get_orden(db, orden_id):
    return SimpleNamespace(id=orden_id, checklists=[])


async def fake_background_pdf(*args, **kwargs):
    return None


def fake_user(role: str = "admin"):
    return SimpleNamespace(
        uid="firebase-smoke-user",
        rol=role,
        role=role,
        company_id=COMPANY_ID,
        created_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def create_smoke_app(monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    monkeypatch.setattr(dashboard, "DashboardService", FakeDashboardService)
    monkeypatch.setattr(dashboard, "OrdenTrabajoService", FakeDashboardOrdenTrabajoService)
    monkeypatch.setattr(ordenes_de_trabajo, "OrdenDeTrabajoService", FakeOrdenDeTrabajoService)
    monkeypatch.setattr(checklists, "ChecklistService", FakeChecklistService)
    monkeypatch.setattr(ordenes_seguimiento, "ChecklistService", FakeChecklistService)
    monkeypatch.setattr(ordenes_seguimiento, "OrdenService", FakeOrdenService)
    monkeypatch.setattr(ordenes_seguimiento, "_get_orden", fake_get_orden)
    monkeypatch.setattr(ordenes_seguimiento, "generar_y_subir_pdf", fake_background_pdf)

    app = FastAPI()
    app.middleware("http")(observability_middleware)
    app.include_router(dashboard.router, prefix="/api/dashboard")
    app.include_router(ordenes_de_trabajo.router, prefix="/api/ordenes-trabajo")
    app.include_router(checklists.router, prefix="/api/checklists")
    app.include_router(ordenes_seguimiento.router, prefix="/api/seguimiento")

    async def fake_db():
        return DummyDB()

    async def fake_auth_dependency(request: Request):
        user = fake_user()
        request.state.current_user = user
        return user

    app.dependency_overrides[get_db] = fake_db
    app.dependency_overrides[get_current_firebase_user] = fake_auth_dependency

    for route in app.routes:
        dependant = getattr(route, "dependant", None)
        if not dependant:
            continue
        for dependency in dependant.dependencies:
            dependency_call = dependency.call
            if getattr(dependency_call, "__name__", "") == "role_dependency":
                app.dependency_overrides[dependency_call] = fake_auth_dependency

    return app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    return TestClient(create_smoke_app(monkeypatch))


def seguimiento_payload(evento: str) -> dict:
    return {
        "evento": evento,
        "lat": 8.9833,
        "lon": -79.5167,
        "timestamp": "2026-01-01T12:00:00Z",
    }


def sync_payload() -> dict:
    return {
        "orden_trabajo_id": str(ORDER_ID),
        "hora_entrada": "2026-01-01T12:00:00Z",
        "hora_salida": "2026-01-01T13:00:00Z",
        "observaciones": "smoke",
        "check_metadata": {},
        "items": [
            {
                "step_number": 1,
                "is_completed": True,
                "evidencia_data": {},
                "comentario": "ok",
            }
        ],
        "lat": 8.9833,
        "lon": -79.5167,
    }


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("GET", "/api/dashboard/technician", None),
        ("GET", "/api/dashboard/supervisorV2", None),
        ("GET", "/api/dashboard/admin", None),
        ("GET", "/api/dashboard/superadmin", None),
        ("GET", "/api/ordenes-trabajo/company/all", None),
        ("GET", "/api/ordenes-trabajo/supervisor/all", None),
        ("GET", f"/api/checklists/{ORDER_ID}/load", None),
        ("GET", f"/api/checklists/{ORDER_ID}", None),
        (
            "PATCH",
            f"/api/checklists/{ORDER_ID}/items/1",
            {"evidencia_data": {}, "comentario": "smoke", "confirm": True},
        ),
        ("POST", f"/api/seguimiento/{ORDER_ID}/iniciar", seguimiento_payload("INICIO")),
        ("POST", f"/api/seguimiento/{ORDER_ID}/reanudar", seguimiento_payload("REANUDACION")),
        ("POST", f"/api/seguimiento/{ORDER_ID}/sync-validar", sync_payload()),
        ("POST", f"/api/seguimiento/{ORDER_ID}/sync-finalizar", sync_payload()),
        ("GET", f"/api/seguimiento/{ORDER_ID}/reporte-prerevision", None),
    ],
)
def test_core_mobile_endpoint_exists_and_keeps_observability_headers(
    client: TestClient,
    method: str,
    path: str,
    json_body: dict | None,
):
    response = client.request(
        method,
        path,
        json=json_body,
        headers={
            "X-Request-ID": "smoke-request-id",
            "X-App-Platform": "ios",
            "X-App-Version": "1.0.0-smoke",
        },
    )

    assert response.status_code not in {404, 405}
    assert response.headers["X-Request-ID"] == "smoke-request-id"
