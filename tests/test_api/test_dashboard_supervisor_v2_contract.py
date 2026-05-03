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
SUPERVISOR_UID = "supervisor-dashboard-contract"
CREATED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

ORDER_CERRADA = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ORDER_PAUSA = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
ORDER_PENDIENTE = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
ORDER_VALIDACION = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
ORDER_EJECUCION = UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")


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
        return FakeOrdersResult(
            [
                fake_order(
                    order_id=ORDER_CERRADA,
                    estado="Cerrada",
                    estado_id=5,
                    fecha=date(2026, 1, 1),
                    descripcion="Orden cerrada",
                ),
                fake_order(
                    order_id=ORDER_PAUSA,
                    estado="En Pausa",
                    estado_id=6,
                    fecha=date(2026, 1, 2),
                    descripcion="Orden en pausa",
                    cliente=None,
                    tecnico=None,
                    unidad=None,
                    prioridad=None,
                    tipo_orden=None,
                ),
                fake_order(
                    order_id=ORDER_PENDIENTE,
                    estado="Pendiente",
                    estado_id=1,
                    fecha=date(2026, 1, 3),
                    descripcion="Orden pendiente",
                ),
                fake_order(
                    order_id=ORDER_VALIDACION,
                    estado="En Validación",
                    estado_id=4,
                    fecha=date(2026, 1, 4),
                    descripcion="Orden por validar",
                ),
                fake_order(
                    order_id=ORDER_EJECUCION,
                    estado="En ejecución",
                    estado_id=3,
                    fecha=date(2026, 1, 5),
                    descripcion="Orden en ejecución",
                ),
            ]
        )

    async def get(self, *args, **kwargs):
        self.get_calls.append((args, kwargs))
        raise AssertionError("dashboard supervisorV2 no debe hacer db.get por fila")


def fake_order(
    *,
    order_id: UUID,
    estado: str,
    estado_id: int,
    fecha: date,
    descripcion: str,
    cliente=SimpleNamespace(display_name="Cliente contrato"),
    tecnico=SimpleNamespace(display_name="Tecnico contrato"),
    unidad=SimpleNamespace(
        nombre="Unidad contrato",
        proyecto=SimpleNamespace(nombre="Proyecto contrato"),
    ),
    prioridad=SimpleNamespace(nombre="Alta"),
    tipo_orden=SimpleNamespace(nombre="Preventivo"),
):
    return SimpleNamespace(
        id=order_id,
        estado_id=estado_id,
        cliente=cliente,
        tecnico=tecnico,
        unidad=unidad,
        descripcion=descripcion,
        observaciones=None,
        estado=SimpleNamespace(nombre=estado),
        fecha=fecha,
        prioridad=prioridad,
        tipo_orden=tipo_orden,
    )


def create_app(db: RecordingDB) -> FastAPI:
    app = FastAPI()
    app.middleware("http")(observability_middleware)
    app.include_router(dashboard.router, prefix="/api/dashboard")

    async def fake_db():
        return db

    async def fake_auth_dependency(request: Request):
        user = SimpleNamespace(
            uid=SUPERVISOR_UID,
            rol="supervisor",
            role="supervisor",
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


def test_dashboard_supervisor_v2_contract_filters_metrics_shape_and_ordering():
    db = RecordingDB()
    client = TestClient(create_app(db))

    response = client.get(
        "/api/dashboard/supervisorV2",
        params={"fecha_inicio": "2026-01-01", "fecha_fin": "2026-01-31"},
        headers={"X-Request-ID": "dashboard-supervisor-v2-contract"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "dashboard-supervisor-v2-contract"
    assert db.get_calls == []
    assert len(db.statements) == 1

    compiled_sql = str(db.statements[0])
    assert "ordenes_de_trabajo.supervisor_id" in compiled_sql
    assert "ordenes_de_trabajo.company_id" in compiled_sql
    assert "ordenes_de_trabajo.fecha" in compiled_sql
    assert "ORDER BY ordenes_de_trabajo.fecha ASC" in compiled_sql
    assert "LIMIT" not in compiled_sql

    params = db.statements[0].compile().params
    assert SUPERVISOR_UID in params.values()
    assert COMPANY_ID in params.values()
    assert date(2026, 1, 1) in params.values()
    assert date(2026, 1, 31) in params.values()

    payload = response.json()
    assert set(payload.keys()) == {
        "ordenes_programadas",
        "ordenes_cerradas",
        "ordenes_por_validar",
        "ordenes_pendientes",
        "ordenes_en_ejecucion",
        "ordenes_atrasadas",
        "cumplimiento_decimal",
        "cumplimiento_label",
        "cumplimiento_str",
        "ordenes",
    }
    assert payload["ordenes_programadas"] == 5
    assert payload["ordenes_cerradas"] == 1
    assert payload["ordenes_por_validar"] == 1
    assert payload["ordenes_pendientes"] == 1
    assert payload["ordenes_en_ejecucion"] == 1
    assert payload["ordenes_atrasadas"] == 1
    assert payload["cumplimiento_decimal"] == 0.2
    assert payload["cumplimiento_str"] == "20%"
    assert payload["cumplimiento_label"] == "1 órdenes cerradas de 5 órdenes totales"

    ordenes = payload["ordenes"]
    assert [orden["id"] for orden in ordenes] == [
        str(ORDER_EJECUCION),
        str(ORDER_PAUSA),
        str(ORDER_PENDIENTE),
        str(ORDER_VALIDACION),
        str(ORDER_CERRADA),
    ]
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
        "id": str(ORDER_EJECUCION),
        "cliente": "Cliente contrato",
        "tecnico": "Tecnico contrato",
        "proyecto": "Proyecto contrato",
        "unidad": "Unidad contrato",
        "descripcion": "Orden en ejecución",
        "observaciones": "",
        "estado": "En ejecución",
        "fecha_programada": "2026-01-05",
        "prioridad": "Alta",
        "tipo_orden": "Preventivo",
    }
    assert ordenes[1]["cliente"] == "—"
    assert ordenes[1]["tecnico"] == "—"
    assert ordenes[1]["proyecto"] == "—"
    assert ordenes[1]["unidad"] == "—"
    assert ordenes[1]["prioridad"] == "—"
    assert ordenes[1]["tipo_orden"] == "—"


def test_dashboard_supervisor_v2_auth_is_required_without_override():
    app = FastAPI()
    app.middleware("http")(observability_middleware)
    app.include_router(dashboard.router, prefix="/api/dashboard")
    client = TestClient(app)

    response = client.get(
        "/api/dashboard/supervisorV2",
        headers={"X-Request-ID": "dashboard-supervisor-v2-auth-contract"},
    )

    assert response.status_code not in {404, 405}
    assert response.status_code in {401, 403}
    assert response.headers["X-Request-ID"] == "dashboard-supervisor-v2-auth-contract"
