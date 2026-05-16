from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.schemas.ordenes_de_trabajo import OrdenDeTrabajoCreate
from app.services.ordenes_de_trabajo import OrdenDeTrabajoService


COMPANY_ID = UUID("33333333-3333-3333-3333-333333333333")
CLIENT_ID = UUID("22222222-2222-2222-2222-222222222222")
UNIT_ID = UUID("44444444-4444-4444-4444-444444444444")


class FakeScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


def make_payload() -> OrdenDeTrabajoCreate:
    return OrdenDeTrabajoCreate(
        descripcion="Mantenimiento preventivo",
        observaciones="Observaciones de prueba",
        valor=None,
        fecha=date(2026, 5, 13),
        tipo_orden_id=1,
        estado_id=1,
        prioridad_id=1,
        unidad_id=UNIT_ID,
        tecnico_id="technician-1",
        supervisor_id="supervisor-1",
    )


def make_user():
    return SimpleNamespace(uid="admin-1", company_id=COMPANY_ID, rol="admin")


def make_reference_error() -> IntegrityError:
    return IntegrityError(
        statement="INSERT INTO ordenes_de_trabajo ...",
        params={},
        orig=Exception(
            'duplicate key value violates unique constraint "ordenes_de_trabajo_referencia_key"'
        ),
    )


def make_other_integrity_error() -> IntegrityError:
    return IntegrityError(
        statement="INSERT INTO ordenes_de_trabajo ...",
        params={},
        orig=Exception('insert or update on table "ordenes_de_trabajo" violates foreign key constraint'),
    )


@pytest.fixture
def service_dependencies(monkeypatch):
    from app.services import ordenes_de_trabajo as service_module

    async def fake_unidad_get(db, unidad_id):
        return SimpleNamespace(id=unidad_id, company_id=COMPANY_ID, cliente_id=CLIENT_ID)

    async def fake_enum_get(db, value):
        return SimpleNamespace(id=value)

    class FakePlanEnforcementService:
        def __init__(self, db):
            self.db = db

        async def assert_can_create_work_order(self, company_id):
            return None

        async def refresh_current_usage_snapshot(self, company_id):
            return None

    monkeypatch.setattr(service_module.unidad_crud, "get", fake_unidad_get)
    monkeypatch.setattr(service_module.tipo_orden_crud, "get", fake_enum_get)
    monkeypatch.setattr(service_module.estado_orden_crud, "get", fake_enum_get)
    monkeypatch.setattr(service_module.prioridad_crud, "get", fake_enum_get)
    monkeypatch.setattr(service_module, "PlanEnforcementService", FakePlanEnforcementService)

    return service_module


@pytest.mark.asyncio
async def test_create_generates_first_reference_of_day(mock_db_session, service_dependencies, monkeypatch):
    added = []
    mock_db_session.execute.side_effect = [FakeScalarResult(None)]
    mock_db_session.add.side_effect = added.append

    service = OrdenDeTrabajoService(mock_db_session)
    monkeypatch.setattr(service, "_reference_prefix_for_today", lambda: "OTC260513")

    await service.create(make_payload(), COMPANY_ID, make_user())

    assert len(added) == 1
    assert added[0].referencia == "OTC2605130001"
    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_once_with(added[0])


@pytest.mark.asyncio
async def test_create_generates_next_reference_when_previous_exists(mock_db_session, service_dependencies, monkeypatch):
    added = []
    mock_db_session.execute.side_effect = [FakeScalarResult("OTC2605130001")]
    mock_db_session.add.side_effect = added.append

    service = OrdenDeTrabajoService(mock_db_session)
    monkeypatch.setattr(service, "_reference_prefix_for_today", lambda: "OTC260513")

    await service.create(make_payload(), COMPANY_ID, make_user())

    assert added[0].referencia == "OTC2605130002"


@pytest.mark.asyncio
async def test_create_does_not_reuse_deleted_reference_gaps(mock_db_session, service_dependencies, monkeypatch):
    added = []
    mock_db_session.execute.side_effect = [FakeScalarResult("OTC2605130004")]
    mock_db_session.add.side_effect = added.append

    service = OrdenDeTrabajoService(mock_db_session)
    monkeypatch.setattr(service, "_reference_prefix_for_today", lambda: "OTC260513")

    await service.create(make_payload(), COMPANY_ID, make_user())

    assert added[0].referencia == "OTC2605130005"


@pytest.mark.asyncio
async def test_create_retries_when_reference_unique_constraint_collides(
    mock_db_session, service_dependencies, monkeypatch
):
    added = []
    mock_db_session.execute.side_effect = [
        FakeScalarResult("OTC2605130006"),
        FakeScalarResult("OTC2605130007"),
    ]
    mock_db_session.commit.side_effect = [make_reference_error(), None]
    mock_db_session.add.side_effect = added.append

    service = OrdenDeTrabajoService(mock_db_session)
    monkeypatch.setattr(service, "_reference_prefix_for_today", lambda: "OTC260513")

    await service.create(make_payload(), COMPANY_ID, make_user())

    assert [orden.referencia for orden in added] == ["OTC2605130007", "OTC2605130008"]
    assert mock_db_session.rollback.await_count == 1
    assert mock_db_session.commit.await_count == 2
    mock_db_session.refresh.assert_awaited_once_with(added[-1])


@pytest.mark.asyncio
async def test_create_returns_409_when_reference_retries_are_exhausted(
    mock_db_session, service_dependencies, monkeypatch
):
    mock_db_session.execute.side_effect = [
        FakeScalarResult("OTC2605130006"),
        FakeScalarResult("OTC2605130007"),
        FakeScalarResult("OTC2605130008"),
    ]
    mock_db_session.commit.side_effect = [
        make_reference_error(),
        make_reference_error(),
        make_reference_error(),
    ]

    service = OrdenDeTrabajoService(mock_db_session)
    monkeypatch.setattr(service, "_reference_prefix_for_today", lambda: "OTC260513")

    with pytest.raises(HTTPException) as exc_info:
        await service.create(make_payload(), COMPANY_ID, make_user())

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == (
        "No fue posible generar una referencia única para la orden de trabajo. Intente nuevamente."
    )
    assert mock_db_session.rollback.await_count == 3
    assert mock_db_session.commit.await_count == 3


@pytest.mark.asyncio
async def test_create_reraises_other_integrity_errors(mock_db_session, service_dependencies, monkeypatch):
    mock_db_session.execute.side_effect = [FakeScalarResult("OTC2605130006")]
    mock_db_session.commit.side_effect = [make_other_integrity_error()]

    service = OrdenDeTrabajoService(mock_db_session)
    monkeypatch.setattr(service, "_reference_prefix_for_today", lambda: "OTC260513")

    with pytest.raises(IntegrityError):
        await service.create(make_payload(), COMPANY_ID, make_user())

    assert mock_db_session.rollback.await_count == 1
    assert mock_db_session.commit.await_count == 1
