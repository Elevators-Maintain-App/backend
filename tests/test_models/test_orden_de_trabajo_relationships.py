import uuid
from types import SimpleNamespace

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import delete, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Cliente,
    Compania,
    Checklist,
    PdfReportGenerationEvent,
    OrdenDeTrabajo,
    Prioridad,
    Proyecto,
    TipoDocumento,
    TipoOrden,
    TipoUnidad,
    Unidad,
)
from app.db.models.enums.estados_orden import EstadoOrden
from app.db.models.usuarios import Rol
from app.db.session import AsyncSessionLocal
from app.services.ordenes_de_trabajo import OrdenDeTrabajoService


TEST_DOCUMENT_TYPE_ID = 996
TEST_UNIT_TYPE_ID = 996
TEST_ORDER_TYPE_ID = 996
TEST_ORDER_STATUS_ID = 996
TEST_PRIORITY_ID = 996
TEST_COMPANY_DOCUMENT_PREFIX = "ORDER-RELATIONSHIP-TEST-"


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

            await session.execute(
                delete(Checklist).where(Checklist.orden_trabajo_id.in_(
                    select(OrdenDeTrabajo.id).where(
                        OrdenDeTrabajo.company_id.in_(company_ids)
                    )
                ))
            )
            await session.execute(
                delete(OrdenDeTrabajo).where(
                    OrdenDeTrabajo.company_id.in_(company_ids)
                )
            )
            await session.execute(
                delete(Unidad).where(Unidad.company_id.in_(company_ids))
            )
            await session.execute(
                delete(Proyecto).where(Proyecto.company_id.in_(company_ids))
            )
            await session.execute(
                delete(Cliente).where(Cliente.compania_id.in_(company_ids))
            )
            await session.execute(
                delete(Compania).where(Compania.id.in_(company_ids))
            )

            await session.execute(
                delete(TipoUnidad).where(TipoUnidad.id == TEST_UNIT_TYPE_ID)
            )
            await session.execute(
                delete(TipoOrden).where(TipoOrden.id == TEST_ORDER_TYPE_ID)
            )
            await session.execute(
                delete(EstadoOrden).where(
                    EstadoOrden.id == TEST_ORDER_STATUS_ID
                )
            )
            await session.execute(
                delete(Prioridad).where(Prioridad.id == TEST_PRIORITY_ID)
            )
            await session.execute(
                delete(TipoDocumento).where(
                    TipoDocumento.id == TEST_DOCUMENT_TYPE_ID
                )
            )
            await session.commit()


async def _ensure_catalogs(session: AsyncSession) -> None:
    if await session.get(TipoDocumento, TEST_DOCUMENT_TYPE_ID) is None:
        session.add(
            TipoDocumento(
                id=TEST_DOCUMENT_TYPE_ID,
                nombre="Documento Test Relación Orden",
            )
        )

    if await session.get(TipoUnidad, TEST_UNIT_TYPE_ID) is None:
        session.add(
            TipoUnidad(
                id=TEST_UNIT_TYPE_ID,
                nombre="Tipo Unidad Test Relación Orden",
            )
        )

    if await session.get(TipoOrden, TEST_ORDER_TYPE_ID) is None:
        session.add(
            TipoOrden(
                id=TEST_ORDER_TYPE_ID,
                nombre="Tipo Orden Test Relación Orden",
            )
        )

    if await session.get(EstadoOrden, TEST_ORDER_STATUS_ID) is None:
        session.add(
            EstadoOrden(
                id=TEST_ORDER_STATUS_ID,
                nombre="Estado Test Relación Orden",
            )
        )

    if await session.get(Prioridad, TEST_PRIORITY_ID) is None:
        session.add(
            Prioridad(
                id=TEST_PRIORITY_ID,
                nombre="Prioridad Test Relación Orden",
            )
        )

    await session.commit()


@pytest.mark.asyncio
async def test_work_order_cliente_relationship_loads_cliente(
    db_session: AsyncSession,
) -> None:
    await _ensure_catalogs(db_session)

    company = Compania(
        id=uuid.uuid4(),
        nombre="Compañía Test Relación Orden",
        documento=f"{TEST_COMPANY_DOCUMENT_PREFIX}{uuid.uuid4()}",
        tipo_documento_id=TEST_DOCUMENT_TYPE_ID,
        email=f"company-{uuid.uuid4()}@test.local",
        telefono="0000000",
        ciudad="Test City",
        direccion="Test Address",
    )
    db_session.add(company)
    await db_session.flush()

    cliente = Cliente(
        id=uuid.uuid4(),
        nombre="Cliente Relación Correcta",
        documento=f"CLI-{uuid.uuid4()}",
        email=f"client-{uuid.uuid4()}@test.local",
        telefono="0000000",
        ciudad="Test City",
        direccion="Test Address",
        tipo_documento_id=TEST_DOCUMENT_TYPE_ID,
        compania_id=company.id,
    )
    db_session.add(cliente)
    await db_session.flush()

    proyecto = Proyecto(
        id=uuid.uuid4(),
        nombre="Proyecto Test Relación Orden",
        direccion="Test Address",
        company_id=company.id,
        cliente_id=cliente.id,
    )
    db_session.add(proyecto)
    await db_session.flush()

    unidad = Unidad(
        id=uuid.uuid4(),
        nombre="Unidad Test Relación Orden",
        proyecto_id=proyecto.id,
        tipo_unidad_id=TEST_UNIT_TYPE_ID,
        company_id=company.id,
        cliente_id=cliente.id,
    )
    db_session.add(unidad)
    await db_session.flush()

    orden = OrdenDeTrabajo(
        id=uuid.uuid4(),
        referencia=f"ORDER-REL-{uuid.uuid4()}",
        descripcion="Orden para validar relación con Cliente",
        tipo_orden_id=TEST_ORDER_TYPE_ID,
        estado_id=TEST_ORDER_STATUS_ID,
        prioridad_id=TEST_PRIORITY_ID,
        company_id=company.id,
        cliente_id=cliente.id,
        supervisor_id="supervisor-test",
        tecnico_id="technician-test",
        unidad_id=unidad.id,
    )
    db_session.add(orden)
    await db_session.commit()

    orden_id = orden.id
    cliente_id = cliente.id
    cliente_nombre = cliente.nombre

    db_session.expire_all()

    result = await db_session.execute(
        select(OrdenDeTrabajo)
        .options(selectinload(OrdenDeTrabajo.cliente))
        .where(OrdenDeTrabajo.id == orden_id)
    )
    loaded_order = result.scalar_one()

    assert loaded_order.cliente is not None
    assert isinstance(loaded_order.cliente, Cliente)
    assert loaded_order.cliente.id == cliente_id
    assert loaded_order.cliente.nombre == cliente_nombre
    assert loaded_order.cliente_id == cliente_id


async def _create_order_with_checklist(
    session: AsyncSession,
    *,
    with_pdf_events: bool,
) -> tuple[OrdenDeTrabajo, Checklist, list[PdfReportGenerationEvent]]:
    await _ensure_catalogs(session)

    company = Compania(
        id=uuid.uuid4(),
        nombre="Compañía Test Eliminación Orden",
        documento=f"{TEST_COMPANY_DOCUMENT_PREFIX}{uuid.uuid4()}",
        tipo_documento_id=TEST_DOCUMENT_TYPE_ID,
        email=f"company-{uuid.uuid4()}@test.local",
        telefono="0000000",
        ciudad="Test City",
        direccion="Test Address",
    )
    session.add(company)
    await session.flush()

    client = Cliente(
        id=uuid.uuid4(),
        nombre="Cliente Test Eliminación Orden",
        documento=f"CLI-{uuid.uuid4()}",
        email=f"client-{uuid.uuid4()}@test.local",
        telefono="0000000",
        ciudad="Test City",
        direccion="Test Address",
        tipo_documento_id=TEST_DOCUMENT_TYPE_ID,
        compania_id=company.id,
    )
    project = Proyecto(
        id=uuid.uuid4(),
        nombre="Proyecto Test Eliminación Orden",
        direccion="Test Address",
        company_id=company.id,
        cliente_id=client.id,
    )
    unit = Unidad(
        id=uuid.uuid4(),
        nombre="Unidad Test Eliminación Orden",
        proyecto_id=project.id,
        tipo_unidad_id=TEST_UNIT_TYPE_ID,
        company_id=company.id,
        cliente_id=client.id,
    )
    order = OrdenDeTrabajo(
        id=uuid.uuid4(),
        referencia=f"ORDER-DELETE-{uuid.uuid4()}",
        descripcion="Orden para eliminación",
        tipo_orden_id=TEST_ORDER_TYPE_ID,
        estado_id=TEST_ORDER_STATUS_ID,
        prioridad_id=TEST_PRIORITY_ID,
        company_id=company.id,
        cliente_id=client.id,
        supervisor_id="supervisor-delete-test",
        tecnico_id="technician-delete-test",
        unidad_id=unit.id,
    )
    checklist = Checklist(id=uuid.uuid4(), orden_trabajo_id=order.id)
    events = []
    if with_pdf_events:
        events = [
            PdfReportGenerationEvent(
                id=uuid.uuid4(),
                company_id=company.id,
                orden_id=order.id,
                checklist_id=checklist.id,
                report_type="final",
                status="success",
            ),
            PdfReportGenerationEvent(
                id=uuid.uuid4(),
                company_id=company.id,
                orden_id=order.id,
                checklist_id=checklist.id,
                report_type="prerevision",
                status="success",
            ),
        ]

    session.add_all([client, project, unit, order, checklist, *events])
    await session.commit()
    return order, checklist, events


def _supervisor_for(order: OrdenDeTrabajo) -> SimpleNamespace:
    return SimpleNamespace(
        uid=order.supervisor_id,
        company_id=order.company_id,
        rol=Rol.SUPERVISOR,
    )


@pytest.mark.asyncio
async def test_pdf_event_checklist_foreign_key_uses_database_cascade(
    db_session: AsyncSession,
) -> None:
    connection = await db_session.connection()

    def get_ondelete(sync_connection) -> str | None:
        foreign_keys = inspect(sync_connection).get_foreign_keys(
            "pdf_report_generation_events"
        )
        checklist_fk = next(
            fk for fk in foreign_keys if fk["constrained_columns"] == ["checklist_id"]
        )
        return checklist_fk.get("options", {}).get("ondelete")

    assert (await connection.run_sync(get_ondelete) or "").upper() == "CASCADE"


@pytest.mark.asyncio
async def test_supervisor_deletes_order_checklist_and_pdf_events(
    db_session: AsyncSession,
) -> None:
    order, checklist, events = await _create_order_with_checklist(
        db_session,
        with_pdf_events=True,
    )
    event_ids = [event.id for event in events]

    await OrdenDeTrabajoService(db_session).delete(order.id, _supervisor_for(order))
    db_session.expire_all()

    assert await db_session.get(OrdenDeTrabajo, order.id) is None
    assert await db_session.get(Checklist, checklist.id) is None
    for event_id in event_ids:
        assert await db_session.get(PdfReportGenerationEvent, event_id) is None


@pytest.mark.asyncio
async def test_supervisor_deletes_order_without_pdf_events(
    db_session: AsyncSession,
) -> None:
    order, checklist, events = await _create_order_with_checklist(
        db_session,
        with_pdf_events=False,
    )

    await OrdenDeTrabajoService(db_session).delete(order.id, _supervisor_for(order))

    assert events == []
    assert await db_session.get(OrdenDeTrabajo, order.id) is None
    assert await db_session.get(Checklist, checklist.id) is None


@pytest.mark.asyncio
async def test_other_company_admin_cannot_delete_order_or_related_data(
    db_session: AsyncSession,
) -> None:
    order, checklist, events = await _create_order_with_checklist(
        db_session,
        with_pdf_events=True,
    )
    other_company_admin = SimpleNamespace(
        uid="other-company-admin",
        company_id=uuid.uuid4(),
        rol=Rol.ADMIN,
    )

    with pytest.raises(HTTPException) as exc_info:
        await OrdenDeTrabajoService(db_session).delete(order.id, other_company_admin)

    assert exc_info.value.status_code == 403
    assert await db_session.get(OrdenDeTrabajo, order.id) is not None
    assert await db_session.get(Checklist, checklist.id) is not None
    for event in events:
        assert await db_session.get(PdfReportGenerationEvent, event.id) is not None


@pytest.mark.asyncio
async def test_technician_cannot_delete_order_or_related_data(
    db_session: AsyncSession,
) -> None:
    order, checklist, events = await _create_order_with_checklist(
        db_session,
        with_pdf_events=True,
    )
    technician = SimpleNamespace(
        uid=order.tecnico_id,
        company_id=order.company_id,
        rol=Rol.TECHNICIAN,
    )

    with pytest.raises(HTTPException) as exc_info:
        await OrdenDeTrabajoService(db_session).delete(order.id, technician)

    assert exc_info.value.status_code == 403
    assert await db_session.get(OrdenDeTrabajo, order.id) is not None
    assert await db_session.get(Checklist, checklist.id) is not None
    for event in events:
        assert await db_session.get(PdfReportGenerationEvent, event.id) is not None
