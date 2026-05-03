from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.api.routes import unidades
from app.auth.firebase import get_current_firebase_user
from app.db.session import get_db
from app.middleware.observability import observability_middleware


COMPANY_ID = UUID("33333333-3333-3333-3333-333333333333")
UNIT_ID_1 = UUID("44444444-4444-4444-4444-444444444444")
UNIT_ID_2 = UUID("55555555-5555-5555-5555-555555555555")
CREATED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
UPDATED_AT = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)


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
                    id=UNIT_ID_1,
                    nombre="Unidad A",
                    kpi_funcionamiento="98%",
                    proyecto="Proyecto A",
                    cliente="Cliente A",
                    tipo_unidad_id=10,
                    tipo_unidad="Ascensor",
                    company_id=COMPANY_ID,
                    created_at=CREATED_AT,
                    updated_at=UPDATED_AT,
                ),
                SimpleNamespace(
                    id=UNIT_ID_2,
                    nombre="Unidad B",
                    kpi_funcionamiento=None,
                    proyecto=None,
                    cliente=None,
                    tipo_unidad_id=20,
                    tipo_unidad=None,
                    company_id=COMPANY_ID,
                    created_at=CREATED_AT,
                    updated_at=UPDATED_AT,
                ),
            ]
        )

    async def get(self, *args, **kwargs):
        self.get_calls.append((args, kwargs))
        raise AssertionError("company/all debe evitar db.get por fila")


def create_app(db: RecordingDB) -> FastAPI:
    app = FastAPI()
    app.middleware("http")(observability_middleware)
    app.include_router(unidades.router, prefix="/api/unidades")

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


def test_unidades_company_all_contract_and_no_per_row_gets():
    db = RecordingDB()
    client = TestClient(create_app(db))

    response = client.get(
        "/api/unidades/company/all",
        headers={"X-Request-ID": "unidades-contract"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "unidades-contract"
    assert db.get_calls == []

    payload = response.json()
    assert [item["id"] for item in payload] == [str(UNIT_ID_1), str(UNIT_ID_2)]
    assert set(payload[0].keys()) == {
        "id",
        "nombre",
        "kpi_funcionamiento",
        "proyecto",
        "cliente",
        "tipo_unidad_id",
        "tipo_unidad",
        "company_id",
        "created_at",
        "updated_at",
    }
    assert payload[0]["proyecto"] == "Proyecto A"
    assert payload[0]["cliente"] == "Cliente A"
    assert payload[0]["tipo_unidad"] == "Ascensor"
    assert payload[1]["proyecto"] == "—"
    assert payload[1]["cliente"] == "—"
    assert payload[1]["tipo_unidad"] == "—"

    compiled = str(db.statements[0])
    assert "unidades.company_id" in compiled
    assert "JOIN proyectos" in compiled
    assert "JOIN clientes" in compiled
    assert "JOIN tipos_unidad" in compiled
