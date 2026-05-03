from __future__ import annotations

from datetime import date, datetime, timezone
from importlib import import_module
from types import SimpleNamespace
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.auth.firebase import get_current_firebase_user
from app.db.session import get_db
from app.middleware.observability import observability_middleware


dashboard = import_module("app.api.routes.dashboard")


COMPANY_ID = UUID("33333333-3333-3333-3333-333333333333")
ORDER_ID_1 = UUID("88888888-8888-8888-8888-888888888888")
ORDER_ID_2 = UUID("99999999-9999-9999-9999-999999999999")
TECHNICIAN_UID = "technician-dashboard-contract"
CREATED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class FakeMetricsResult:
    def one(self):
        return SimpleNamespace(total=4, completadas=1, pendientes=3)


class FakeScalars:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class FakeOrdersResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return FakeScalars(self._rows)


class RecordingDB:
    def __init__(self):
        self.statements = []
        self.get_calls = []

    async def execute(self, statement):
        self.statements.append(statement)
        if len(self.statements) == 1:
            return FakeMetricsResult()
        return FakeOrdersResult(
            [
                fake_order(
                    order_id=ORDER_ID_1,
                    estado="Pendiente",
                    estado_id=1,
                    fecha=date(2026, 1, 10),
                    descripcion="Orden pendiente",
                ),
                fake_order(
                    order_id=ORDER_ID_2,
                    estado="En ejecución",
                    estado_id=3,
                    fecha=date(2026, 1, 11),
                    descripcion="Orden en ejecución",
                ),
            ]
        )

    async def get(self, *args, **kwargs):
        self.get_calls.append((args, kwargs))
        raise AssertionError("dashboard technician no debe hacer db.get por fila")


def fake_order(
    *,
    order_id: UUID,
    estado: str,
    estado_id: int,
    fecha: date,
    descripcion: str,
):
    return SimpleNamespace(
        id=order_id,
        estado_id=estado_id,
        cliente=SimpleNamespace(display_name="Cliente contrato"),
        tecnico=SimpleNamespace(display_name="Tecnico contrato"),
        unidad=SimpleNamespace(
            nombre="Unidad contrato",
            proyecto=SimpleNamespace(nombre="Proyecto contrato"),
        ),
        descripcion=descripcion,
        observaciones=None,
        estado=SimpleNamespace(nombre=estado),
        fecha=fecha,
        prioridad=SimpleNamespace(nombre="Alta"),
        tipo_orden=SimpleNamespace(nombre="Preventivo"),
    )


def create_app(db: RecordingDB) -> FastAPI:
    app = FastAPI()
    app.middleware("http")(observability_middleware)
    app.include_router(dashboard.router, prefix="/api/dashboard")

    async def fake_db():
        return db

    async def fake_auth_dependency(request: Request):
        user = SimpleNamespace(
            uid=TECHNICIAN_UID,
            rol="technician",
            role="technician",
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


def test_dashboard_technician_contract_filters_metrics_shape_and_ordering():
    db = RecordingDB()
    client = TestClient(create_app(db))

    response = client.get(
        "/api/dashboard/technician",
        params={"fecha_inicio": "2026-01-01", "fecha_fin": "2026-01-31"},
        headers={"X-Request-ID": "dashboard-technician-contract"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "dashboard-technician-contract"
    assert db.get_calls == []
    assert len(db.statements) == 2

    metricas_sql = str(db.statements[0])
    ordenes_sql = str(db.statements[1])
    assert "count" in metricas_sql.lower()
    assert "estado_id" in metricas_sql
    assert "ordenes_de_trabajo.tecnico_id" in metricas_sql
    assert "ordenes_de_trabajo.company_id" in metricas_sql
    assert "ordenes_de_trabajo.fecha" in metricas_sql
    assert "ORDER BY" not in metricas_sql
    assert "ORDER BY ordenes_de_trabajo.fecha ASC" in ordenes_sql

    metricas_params = db.statements[0].compile().params
    assert TECHNICIAN_UID in metricas_params.values()
    assert str(COMPANY_ID) in metricas_params.values()
    assert date(2026, 1, 1) in metricas_params.values()
    assert date(2026, 1, 31) in metricas_params.values()

    payload = response.json()
    assert set(payload.keys()) == {
        "ordenes_programadas",
        "ordenes_completadas",
        "ordenes_pendientes",
        "cumplimiento_decimal",
        "cumplimiento_label",
        "ordenes_en_curso",
        "cumplimiento_str",
    }
    assert payload["ordenes_programadas"] == 4
    assert payload["ordenes_completadas"] == 1
    assert payload["ordenes_pendientes"] == 3
    assert payload["cumplimiento_decimal"] == 0.25
    assert payload["cumplimiento_str"] == "25%"
    assert payload["cumplimiento_label"] == "1 órdenes completadas de 4 órdenes totales"

    ordenes = payload["ordenes_en_curso"]
    assert [orden["id"] for orden in ordenes] == [str(ORDER_ID_2), str(ORDER_ID_1)]
    assert set(ordenes[0].keys()) == {
        "id",
        "cliente",
        "tecnico",
        "proyecto",
        "unidad",
        "descripcion",
        "observaciones",
        "estado",
        "fecha_programada",
        "prioridad",
        "tipo_orden",
    }
    assert ordenes[0] == {
        "id": str(ORDER_ID_2),
        "cliente": "Cliente contrato",
        "tecnico": "Tecnico contrato",
        "proyecto": "Proyecto contrato",
        "unidad": "Unidad contrato",
        "descripcion": "Orden en ejecución",
        "observaciones": "",
        "estado": "En ejecución",
        "fecha_programada": "2026-01-11",
        "prioridad": "Alta",
        "tipo_orden": "Preventivo",
    }


def test_dashboard_technician_auth_is_required_without_override():
    app = FastAPI()
    app.middleware("http")(observability_middleware)
    app.include_router(dashboard.router, prefix="/api/dashboard")
    client = TestClient(app)

    response = client.get(
        "/api/dashboard/technician",
        headers={"X-Request-ID": "dashboard-technician-auth-contract"},
    )

    assert response.status_code not in {404, 405}
    assert response.status_code in {401, 403}
    assert response.headers["X-Request-ID"] == "dashboard-technician-auth-contract"
