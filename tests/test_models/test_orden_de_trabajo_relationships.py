import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Cliente,
    Compania,
    OrdenDeTrabajo,
    Prioridad,
    Proyecto,
    TipoDocumento,
    TipoOrden,
    TipoUnidad,
    Unidad,
)
from app.db.models.enums.estados_orden import EstadoOrden
from app.db.session import AsyncSessionLocal


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