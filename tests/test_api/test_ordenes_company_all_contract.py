from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.api.routes import ordenes_de_trabajo
from app.auth.firebase import get_current_firebase_user
from app.db.session import get_db
from app.middleware.observability import observability_middleware


COMPANY_ID = UUID("33333333-3333-3333-3333-333333333333")
ORDER_ID_1 = UUID("66666666-6666-6666-6666-666666666666")
ORDER_ID_2 = UUID("77777777-7777-7777-7777-777777777777")
UNIT_ID_1 = UUID("44444444-4444-4444-4444-444444444444")
UNIT_ID_2 = UUID("55555555-5555-5555-5555-555555555555")
CREATED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class RecordingDB:
    def __init__(self):
        self.statements = []
        self.get_calls = []

    async def execute(self, statement):
        self.statements.append(statement)
        return FakeResult(
            [
                SimpleNamespace(
                    id=ORDER_ID_1,
                    referencia="OT-001",
                    fecha=date(2026, 1, 10),
                    supervisor_id="supervisor-1",
                    tecnico_id="technician-1",
                    unidad_id=UNIT_ID_1,
                    company_id=COMPANY_ID,
                    tipo_orden_id=10,
                    estado_id=20,
                    prioridad_id=30,
                ),
                SimpleNamespace(
                    id=ORDER_ID_2,
                    referencia="OT-002",
                    fecha=None,
                    supervisor_id="supervisor-2",
                    tecnico_id="technician-2",
                    unidad_id=UNIT_ID_2,
                    company_id=COMPANY_ID,
                    tipo_orden_id=11,
                    estado_id=21,
                    prioridad_id=31,
                ),
            ]
        )

    async def get(self, *args, **kwargs):
        self.get_calls.append((args, kwargs))
        raise AssertionError("company/all no debe hacer db.get por fila")


def create_app(db: RecordingDB) -> FastAPI:
    app = FastAPI()
    app.middleware("http")(observability_middleware)
    app.include_router(ordenes_de_trabajo.router, prefix="/api/ordenes-trabajo")

    async def fake_db():
        return db

    async def fake_auth_dependency(request: Request):
        user = SimpleNamespace(
            uid="admin-smoke",
            rol="admin",
            role="admin",
            company_id=COMPANY_ID,
            created_time=CREATED_AT,
        )
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


def test_ordenes_company_all_contract_company_filter_and_shape():
    db = RecordingDB()
    client = TestClient(create_app(db))

    response = client.get(
        "/api/ordenes-trabajo/company/all",
        headers={"X-Request-ID": "ordenes-contract"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "ordenes-contract"
    assert db.get_calls == []

    payload = response.json()
    assert [item["id"] for item in payload] == [str(ORDER_ID_1), str(ORDER_ID_2)]
    assert set(payload[0].keys()) == {
        "id",
        "referencia",
        "fecha",
        "supervisor_id",
        "tecnico_id",
        "unidad_id",
        "company_id",
        "tipo_orden_id",
        "estado_id",
        "prioridad_id",
    }
    assert payload[0] == {
        "id": str(ORDER_ID_1),
        "referencia": "OT-001",
        "fecha": "2026-01-10",
        "supervisor_id": "supervisor-1",
        "tecnico_id": "technician-1",
        "unidad_id": str(UNIT_ID_1),
        "company_id": str(COMPANY_ID),
        "tipo_orden_id": 10,
        "estado_id": 20,
        "prioridad_id": 30,
    }
    assert payload[1]["fecha"] is None

    compiled = str(db.statements[0])
    assert "ordenes_de_trabajo.company_id" in compiled
    assert "ORDER BY" not in compiled
    assert "LIMIT" in compiled


def test_ordenes_company_all_auth_is_required_without_override():
    app = FastAPI()
    app.middleware("http")(observability_middleware)
    app.include_router(ordenes_de_trabajo.router, prefix="/api/ordenes-trabajo")
    client = TestClient(app)

    response = client.get(
        "/api/ordenes-trabajo/company/all",
        headers={"X-Request-ID": "ordenes-auth-contract"},
    )

    assert response.status_code not in {404, 405}
    assert response.status_code in {401, 403}
    assert response.headers["X-Request-ID"] == "ordenes-auth-contract"
