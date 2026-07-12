import asyncio
from datetime import date, datetime, time, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models.compania import Compania
from app.db.models.overtime_requests import OvertimeRequest, OvertimeRequestStatus
from app.db.models.proyectos import Proyecto
from app.db.models.enums.tipos_documento import TipoDocumento
from app.db.models.usuarios import Rol, Usuario
from app.db.session import AsyncSessionLocal
from app.db.repositories.overtime_requests import OvertimeRequestRepository
from app.schemas.overtime_requests import OvertimeApproveRequest, OvertimeRequestUpdate
from app.services.overtime.request_service import OvertimeRequestService


class _BinaryRenderer:
    def __init__(self, content):
        self.content = content

    def render(self, context):
        return self.content


def _request(*, company_id, technician_id, project_id, supervisor_id, entry, exit):
    now = datetime.now(timezone.utc)
    worked_minutes = int(
        (datetime.combine(date.min, exit) - datetime.combine(date.min, entry)).total_seconds()
        // 60
    )
    return OvertimeRequest(
        company_id=company_id,
        technician_id=technician_id,
        work_date=date(2026, 7, 8),
        entry_time=entry,
        exit_time=exit,
        activity="Prueba de concurrencia",
        project_id=project_id,
        authorizing_supervisor_id=supervisor_id,
        worked_minutes=worked_minutes,
        regular_minutes=min(worked_minutes, 480),
        overtime_minutes=max(worked_minutes - 480, 0),
        status=OvertimeRequestStatus.PENDING,
        submitted_at=now,
        created_at=now,
        updated_at=now,
    )


async def _seed_request(*, entry=time(8), exit=time(11)):
    suffix = uuid4().hex
    document_type_id = int(suffix[:6], 16)
    async with AsyncSessionLocal() as setup:
        document_type = TipoDocumento(id=document_type_id, nombre=f"Test {suffix}")
        company = Compania(
            nombre="Compañía concurrencia",
            tipo_documento_id=document_type_id,
            documento=f"company-{suffix}",
        )
        setup.add_all([document_type, company])
        await setup.flush()
        technician = Usuario(
            uid=f"tech-{suffix}", display_name="Técnico", company_id=company.id,
            document_id=f"tech-doc-{suffix}", document_type_id=document_type_id,
            email=f"tech-{suffix}@example.com", rol=Rol.TECHNICIAN, is_active=True,
        )
        supervisor = Usuario(
            uid=f"supervisor-{suffix}", display_name="Supervisor", company_id=company.id,
            document_id=f"supervisor-doc-{suffix}", document_type_id=document_type_id,
            email=f"supervisor-{suffix}@example.com", rol=Rol.SUPERVISOR, is_active=True,
        )
        project = Proyecto(nombre="Proyecto concurrencia", company_id=company.id)
        setup.add_all([technician, supervisor, project])
        await setup.flush()
        request = _request(
            company_id=company.id, technician_id=technician.id, project_id=project.id,
            supervisor_id=supervisor.id, entry=entry, exit=exit,
        )
        setup.add(request)
        await setup.commit()
        return request.id, technician.uid, supervisor.uid


@pytest.mark.asyncio
async def test_concurrent_overlapping_requests_cannot_both_commit():
    suffix = uuid4().hex
    document_type_id = int(suffix[:6], 16)
    async with AsyncSessionLocal() as setup:
        document_type = TipoDocumento(id=document_type_id, nombre=f"Test {suffix}")
        company = Compania(
            nombre="Compañía concurrencia",
            tipo_documento_id=document_type_id,
            documento=f"company-{suffix}",
        )
        setup.add_all([document_type, company])
        await setup.flush()
        technician = Usuario(
            uid=f"tech-{suffix}", display_name="Técnico", company_id=company.id,
            document_id=f"tech-doc-{suffix}", document_type_id=document_type_id,
            email=f"tech-{suffix}@example.com", rol=Rol.TECHNICIAN, is_active=True,
        )
        supervisor = Usuario(
            uid=f"supervisor-{suffix}", display_name="Supervisor", company_id=company.id,
            document_id=f"supervisor-doc-{suffix}", document_type_id=document_type_id,
            email=f"supervisor-{suffix}@example.com", rol=Rol.SUPERVISOR, is_active=True,
        )
        project = Proyecto(nombre="Proyecto concurrencia", company_id=company.id)
        setup.add_all([technician, supervisor, project])
        await setup.commit()
        ids = company.id, technician.id, project.id, supervisor.id

    first = AsyncSessionLocal()
    second = AsyncSessionLocal()
    try:
        first.add(
            _request(
                company_id=ids[0], technician_id=ids[1], project_id=ids[2],
                supervisor_id=ids[3], entry=time(8), exit=time(11),
            )
        )
        await first.flush()

        async def insert_second():
            second.add(
                _request(
                    company_id=ids[0], technician_id=ids[1], project_id=ids[2],
                    supervisor_id=ids[3], entry=time(10), exit=time(12),
                )
            )
            await second.flush()
            await second.commit()

        second_attempt = asyncio.create_task(insert_second())
        await asyncio.sleep(0)
        await first.commit()

        with pytest.raises(IntegrityError) as exc:
            await second_attempt
        assert (
            OvertimeRequestService._constraint_name(exc.value)
            == "excl_overtime_requests_active_overlap"
        )
        await second.rollback()
    finally:
        await first.close()
        await second.close()


@pytest.mark.asyncio
async def test_cancel_and_approve_concurrently_cannot_confirm_both_transitions():
    request_id, technician_uid, supervisor_uid = await _seed_request()
    cancel_session = AsyncSessionLocal()
    approve_session = AsyncSessionLocal()
    try:
        cancelled = await OvertimeRequestService(cancel_session).cancel_own_request(
            SimpleNamespace(uid=technician_uid), request_id
        )
        assert cancelled.status == OvertimeRequestStatus.CANCELLED

        approve_attempt = asyncio.create_task(
            OvertimeRequestService(approve_session).approve(
                SimpleNamespace(uid=supervisor_uid), request_id, OvertimeApproveRequest()
            )
        )
        await asyncio.sleep(0)
        await cancel_session.commit()

        with pytest.raises(HTTPException) as exc:
            await approve_attempt
        assert exc.value.status_code == 409
        await approve_session.rollback()
    finally:
        await cancel_session.close()
        await approve_session.close()


@pytest.mark.asyncio
async def test_edit_and_cancel_serialize_with_coherent_event_order():
    request_id, technician_uid, _ = await _seed_request()
    edit_session = AsyncSessionLocal()
    cancel_session = AsyncSessionLocal()
    auth = SimpleNamespace(uid=technician_uid)
    try:
        edited = await OvertimeRequestService(edit_session).update_own_request(
            auth, request_id, OvertimeRequestUpdate(activity="Actividad editada")
        )
        assert edited.status == OvertimeRequestStatus.PENDING

        cancel_attempt = asyncio.create_task(
            OvertimeRequestService(cancel_session).cancel_own_request(auth, request_id)
        )
        await asyncio.sleep(0)
        await edit_session.commit()
        cancelled = await cancel_attempt
        await cancel_session.commit()

        assert cancelled.status == OvertimeRequestStatus.CANCELLED
        event_types = [event.event_type.value for event in cancelled.events]
        assert event_types[-2:] == ["edited", "cancelled"]
    finally:
        await edit_session.close()
        await cancel_session.close()


@pytest.mark.asyncio
async def test_cancelled_request_releases_equivalent_interval_in_postgresql():
    request_id, technician_uid, _ = await _seed_request()
    async with AsyncSessionLocal() as session:
        await OvertimeRequestService(session).cancel_own_request(
            SimpleNamespace(uid=technician_uid), request_id
        )
        await session.commit()
        cancelled = await session.get(OvertimeRequest, request_id)
        replacement = _request(
            company_id=cancelled.company_id,
            technician_id=cancelled.technician_id,
            project_id=cancelled.project_id,
            supervisor_id=cancelled.authorizing_supervisor_id,
            entry=cancelled.entry_time,
            exit=cancelled.exit_time,
        )
        session.add(replacement)
        await session.commit()
        assert replacement.id is not None


@pytest.mark.asyncio
async def test_database_rejects_edit_toward_an_occupied_interval():
    request_id, _, _ = await _seed_request(entry=time(8), exit=time(10))
    async with AsyncSessionLocal() as setup:
        first = await setup.get(OvertimeRequest, request_id)
        second = _request(
            company_id=first.company_id,
            technician_id=first.technician_id,
            project_id=first.project_id,
            supervisor_id=first.authorizing_supervisor_id,
            entry=time(10),
            exit=time(12),
        )
        setup.add(second)
        await setup.commit()
        second_id = second.id

    async with AsyncSessionLocal() as editing:
        row = (
            await editing.execute(
                select(OvertimeRequest).where(OvertimeRequest.id == second_id).with_for_update()
            )
        ).scalar_one()
        row.entry_time = time(9)
        row.worked_minutes = 180
        row.regular_minutes = 180
        with pytest.raises(IntegrityError) as exc:
            await editing.flush()
        assert (
            OvertimeRequestService._constraint_name(exc.value)
            == "excl_overtime_requests_active_overlap"
        )
        await editing.rollback()


@pytest.mark.asyncio
async def test_paginated_repository_count_order_and_tenant_identity_isolation():
    first_id, technician_uid, _ = await _seed_request(entry=time(8), exit=time(10))
    await _seed_request(entry=time(8), exit=time(10))  # otra compañía, nunca visible
    fixed_submitted_at = datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc)
    async with AsyncSessionLocal() as setup:
        first = await setup.get(OvertimeRequest, first_id)
        technician = (
            await setup.execute(select(Usuario).where(Usuario.uid == technician_uid))
        ).scalar_one()
        first.submitted_at = fixed_submitted_at
        second = _request(
            company_id=first.company_id,
            technician_id=technician.id,
            project_id=first.project_id,
            supervisor_id=first.authorizing_supervisor_id,
            entry=time(10),
            exit=time(12),
        )
        second.submitted_at = fixed_submitted_at
        setup.add(second)
        await setup.commit()
        second_id = second.id
        expected_first_id = max(first.id, second.id)

    async with AsyncSessionLocal() as querying:
        repository = OvertimeRequestRepository(querying)
        rows, total = await repository.page_for_technician(
            company_id=technician.company_id,
            technician_id=technician.id,
            status=None,
            date_from=date(2026, 7, 8),
            date_to=date(2026, 7, 8),
            offset=0,
            limit=1,
        )
        assert total == 2
        assert [row.id for row in rows] == [expected_first_id]
        first = await querying.get(OvertimeRequest, first_id)
        export_filters = {
            "company_id": first.company_id,
            "supervisor_id": first.authorizing_supervisor_id,
            "technician_id": first.technician_id,
            "status": None,
            "date_from": date(2026, 7, 8),
            "date_to": date(2026, 7, 8),
        }
        assert await repository.count_for_supervisor_export(**export_filters) == 2
        exported = await repository.list_for_supervisor_export(**export_filters)
        assert {row.id for row in exported} == {first_id, second_id}


@pytest.mark.asyncio
async def test_supervisor_catalog_ids_filter_page_and_both_exports_without_tenant_leaks():
    request_id, technician_uid, supervisor_uid = await _seed_request()
    other_request_id, other_technician_uid, _ = await _seed_request()
    async with AsyncSessionLocal() as setup:
        request = await setup.get(OvertimeRequest, request_id)
        technician = (
            await setup.execute(select(Usuario).where(Usuario.uid == technician_uid))
        ).scalar_one()
        supervisor = (
            await setup.execute(select(Usuario).where(Usuario.uid == supervisor_uid))
        ).scalar_one()
        other_technician = (
            await setup.execute(select(Usuario).where(Usuario.uid == other_technician_uid))
        ).scalar_one()
        no_request = Usuario(
            uid=f"no-request-{uuid4().hex}", display_name="Técnico sin solicitudes",
            company_id=supervisor.company_id, document_id=f"doc-{uuid4().hex}",
            document_type_id=supervisor.document_type_id,
            email=f"no-request-{uuid4().hex}@example.com", rol=Rol.TECHNICIAN, is_active=True,
        )
        inactive = Usuario(
            uid=f"inactive-{uuid4().hex}", display_name="Técnico inactivo",
            company_id=supervisor.company_id, document_id=f"doc-{uuid4().hex}",
            document_type_id=supervisor.document_type_id,
            email=f"inactive-{uuid4().hex}@example.com", rol=Rol.TECHNICIAN, is_active=False,
        )
        setup.add_all([no_request, inactive])
        await setup.commit()
        ids = technician.id, no_request.id, inactive.id, other_technician.id
        work_date = request.work_date

    async with AsyncSessionLocal() as querying:
        service = OvertimeRequestService(
            querying,
            clock=lambda: datetime(2026, 7, 12, tzinfo=timezone.utc),
            pdf_renderer=_BinaryRenderer(b"%PDF-catalog"),
            xlsx_renderer=_BinaryRenderer(b"PK-catalog"),
        )
        auth = SimpleNamespace(uid=supervisor_uid)
        catalog = await service.list_technician_catalog_for_supervisor(auth)
        catalog_ids = {item.id for item in catalog}
        assert ids[0] in catalog_ids and ids[1] in catalog_ids
        assert ids[2] not in catalog_ids and ids[3] not in catalog_ids
        assert all(item.model_dump().keys() == {"id", "name"} for item in catalog)

        page = await service.page_assigned_requests(
            auth, status=None, technician_id=ids[0], date_from=work_date,
            date_to=work_date, page=1, page_size=20,
        )
        assert page.total == 1 and [item.id for item in page.items] == [request_id]

        empty_same_company = await service.page_assigned_requests(
            auth, status=None, technician_id=ids[1], date_from=work_date,
            date_to=work_date, page=1, page_size=20,
        )
        empty_other_company = await service.page_assigned_requests(
            auth, status=None, technician_id=ids[3], date_from=work_date,
            date_to=work_date, page=1, page_size=20,
        )
        assert empty_same_company.total == empty_other_company.total == 0

        for export_format, prefix in (("pdf", b"%PDF"), ("xlsx", b"PK")):
            content, _, _ = await service.export_assigned_requests(
                auth, export_format=export_format, status=None, technician_id=ids[0],
                date_from=work_date, date_to=work_date,
            )
            assert content.startswith(prefix)

        assert other_request_id != request_id
