from datetime import date, datetime, time, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.db.models.overtime_requests import OvertimeRequest, OvertimeRequestEventType, OvertimeRequestStatus
from app.db.models.proyectos import Proyecto
from app.db.models.usuarios import Rol, Usuario
from app.schemas.overtime_requests import (
    OvertimeAdjustAndApproveRequest,
    OvertimeApproveRequest,
    OvertimeRejectRequest,
    OvertimeRequestCreate,
    OvertimeRequestUpdate,
)
from app.services.overtime.request_service import OvertimeRequestService


NOW = datetime(2026, 7, 8, 15, 0, tzinfo=timezone.utc)
COMPANY_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_COMPANY_ID = UUID("22222222-2222-2222-2222-222222222222")
TECHNICIAN_ID = UUID("33333333-3333-3333-3333-333333333333")
SUPERVISOR_ID = UUID("44444444-4444-4444-4444-444444444444")
PROJECT_ID = UUID("55555555-5555-5555-5555-555555555555")


def user(user_id, role, *, company_id=COMPANY_ID, active=True, uid="uid", name="User"):
    return Usuario(
        id=user_id, uid=uid, rol=role, company_id=company_id,
        is_active=active, display_name=name
    )


TECHNICIAN = user(TECHNICIAN_ID, Rol.TECHNICIAN, name="Técnico")
SUPERVISOR = user(SUPERVISOR_ID, Rol.SUPERVISOR, uid="supervisor-uid", name="Supervisor")
PROJECT = Proyecto(id=PROJECT_ID, company_id=COMPANY_ID, nombre="Proyecto activo")


def auth(uid="uid"):
    return SimpleNamespace(uid=uid)


def create_payload(**changes):
    data = {
        "work_date": date(2026, 7, 8),
        "entry_time": time(7),
        "break_start_time": time(12),
        "break_end_time": time(12, 30),
        "exit_time": time(16, 30),
        "activity": "Mantenimiento preventivo",
        "project_id": PROJECT_ID,
        "authorizing_supervisor_id": SUPERVISOR_ID,
    }
    data.update(changes)
    return OvertimeRequestCreate(**data)


def pending_request():
    row = OvertimeRequest(
        id=uuid4(), company_id=COMPANY_ID, technician_id=TECHNICIAN_ID,
        work_date=date(2026, 7, 8), entry_time=time(7), break_start_time=time(12),
        break_end_time=time(12, 30), exit_time=time(16, 30),
        activity="Actividad original", project_id=PROJECT_ID,
        authorizing_supervisor_id=SUPERVISOR_ID, worked_minutes=540,
        regular_minutes=480, overtime_minutes=60, status=OvertimeRequestStatus.PENDING,
        submitted_at=NOW, created_at=NOW, updated_at=NOW,
    )
    row.project = PROJECT
    row.technician = TECHNICIAN
    row.authorizing_supervisor = SUPERVISOR
    row.events = []
    return row


class FakeDB:
    def __init__(self):
        self.commit_calls = 0

    async def commit(self):
        self.commit_calls += 1


class FakeRepository:
    def __init__(self):
        self.users = {"uid": TECHNICIAN, "supervisor-uid": SUPERVISOR}
        self.project = PROJECT
        self.supervisor = SUPERVISOR
        self.technicians = [TECHNICIAN]
        self.request = pending_request()
        self.events = []
        self.created_requests = []
        self.fail_event = False
        self.list_kwargs = None
        self.lock_kwargs = None
        self.overlap = False
        self.overlap_kwargs = None
        self.create_error = None
        self.page_rows = [self.request]
        self.page_total = 1
        self.export_total = 1
        self.export_rows = [self.request]
        self.export_list_calls = 0

    async def get_user_by_uid(self, uid):
        return self.users.get(uid)

    async def list_active_projects(self, company_id):
        return [self.project] if self.project and self.project.company_id == company_id else []

    async def list_active_supervisors(self, company_id):
        return [self.supervisor] if self.supervisor and self.supervisor.company_id == company_id else []

    async def list_active_technicians(self, company_id):
        self.list_kwargs = {"company_id": company_id}
        return [user for user in self.technicians if user.company_id == company_id]

    async def get_active_project(self, company_id, project_id):
        if self.project and self.project.company_id == company_id and self.project.id == project_id:
            return self.project
        return None

    async def get_active_supervisor(self, company_id, user_id):
        candidate = self.supervisor
        if (
            candidate and candidate.company_id == company_id and candidate.id == user_id
            and candidate.rol == Rol.SUPERVISOR and candidate.is_active
        ):
            return candidate
        return None

    async def create_request(self, request):
        if self.create_error is not None:
            raise self.create_error
        request.id = request.id or uuid4()
        self.created_requests.append(request)
        return request

    async def has_active_overlap(self, **kwargs):
        self.overlap_kwargs = kwargs
        return self.overlap

    async def create_event(self, event):
        if self.fail_event:
            raise self.fail_event if isinstance(self.fail_event, Exception) else RuntimeError("audit failed")
        event.id = event.id or uuid4()
        self.events.append(event)
        return event

    async def list_for_technician(self, **kwargs):
        self.list_kwargs = kwargs
        return [self.request]

    async def get_for_technician(self, **kwargs):
        self.list_kwargs = kwargs
        return self.request

    async def list_for_supervisor(self, **kwargs):
        self.list_kwargs = kwargs
        return [self.request]

    async def get_for_supervisor(self, **kwargs):
        self.list_kwargs = kwargs
        return self.request

    async def lock_for_supervisor_review(self, **kwargs):
        self.lock_kwargs = kwargs
        return self.request

    async def lock_for_technician_mutation(self, **kwargs):
        self.lock_kwargs = kwargs
        return self.request

    async def page_for_technician(self, **kwargs):
        self.list_kwargs = kwargs
        return self.page_rows, self.page_total

    async def page_for_supervisor(self, **kwargs):
        self.list_kwargs = kwargs
        return self.page_rows, self.page_total

    async def count_for_supervisor_export(self, **kwargs):
        self.list_kwargs = kwargs
        return self.export_total

    async def list_for_supervisor_export(self, **kwargs):
        self.export_list_calls += 1
        self.list_kwargs = kwargs
        return self.export_rows


def service(repo=None, clock=None):
    repository = repo or FakeRepository()
    db = FakeDB()
    return OvertimeRequestService(db, repository=repository, clock=clock or (lambda: NOW)), repository, db


class FakePdfRenderer:
    def __init__(self):
        self.context = None
        self.calls = 0

    def render(self, context):
        self.context = context
        self.calls += 1
        return b"%PDF-fake"


class FakeXlsxRenderer(FakePdfRenderer):
    def render(self, context):
        self.context = context
        self.calls += 1
        return b"PK-xlsx-fake"


@pytest.mark.asyncio
async def test_technician_creates_request_and_backend_calculates_minutes_with_submitted_event():
    svc, repo, db = service()
    result = await svc.create_request(auth(), create_payload())
    created = repo.created_requests[0]
    assert (created.worked_minutes, created.regular_minutes, created.overtime_minutes) == (540, 480, 60)
    assert created.technician_id == TECHNICIAN_ID
    assert created.company_id == COMPANY_ID
    assert created.status == OvertimeRequestStatus.PENDING
    assert result.events[0].event_type == OvertimeRequestEventType.SUBMITTED
    assert result.events[0].previous_status is None
    assert repo.events[0].snapshot_after["status"] == "pending"
    assert db.commit_calls == 0
    assert repo.overlap_kwargs == {
        "company_id": COMPANY_ID,
        "technician_id": TECHNICIAN_ID,
        "work_date": date(2026, 7, 8),
        "entry_time": time(7),
        "exit_time": time(16, 30),
    }


@pytest.mark.asyncio
async def test_creation_returns_stable_409_when_precheck_finds_active_overlap():
    svc, repo, _ = service()
    repo.overlap = True

    with pytest.raises(HTTPException) as exc:
        await svc.create_request(auth(), create_payload())

    assert exc.value.status_code == 409
    assert exc.value.detail == OvertimeRequestService.ACTIVE_OVERLAP_DETAIL
    assert repo.created_requests == []


class _Diag:
    def __init__(self, constraint_name):
        self.constraint_name = constraint_name


class _OriginalDBError(Exception):
    def __init__(self, constraint_name):
        self.diag = _Diag(constraint_name)


def integrity_error(constraint_name):
    return IntegrityError("insert", {}, _OriginalDBError(constraint_name))


@pytest.mark.asyncio
async def test_creation_translates_only_overlap_constraint_violation_to_same_409():
    svc, repo, _ = service()
    repo.create_error = integrity_error(OvertimeRequestService.ACTIVE_OVERLAP_CONSTRAINT)

    with pytest.raises(HTTPException) as exc:
        await svc.create_request(auth(), create_payload())

    assert exc.value.status_code == 409
    assert exc.value.detail == OvertimeRequestService.ACTIVE_OVERLAP_DETAIL
    assert repo.events == []


@pytest.mark.asyncio
async def test_creation_does_not_translate_unrelated_integrity_error():
    svc, repo, _ = service()
    repo.create_error = integrity_error("some_other_constraint")

    with pytest.raises(IntegrityError):
        await svc.create_request(auth(), create_payload())


def test_create_schema_rejects_client_owned_and_calculated_fields():
    for field, value in (
        ("technician_id", TECHNICIAN_ID), ("company_id", COMPANY_ID),
        ("status", "approved"), ("worked_minutes", 999),
        ("regular_minutes", 999), ("overtime_minutes", 999),
        ("reviewed_at", NOW), ("reviewed_by_user_id", SUPERVISOR_ID),
        ("supervisor_note", "x"),
    ):
        with pytest.raises(ValidationError):
            create_payload(**{field: value})


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid", ["project", "supervisor"])
async def test_creation_rejects_project_or_supervisor_outside_company(invalid):
    svc, repo, _ = service()
    if invalid == "project":
        repo.project = Proyecto(id=PROJECT_ID, company_id=OTHER_COMPANY_ID, nombre="Otro")
    else:
        repo.supervisor = user(SUPERVISOR_ID, Rol.SUPERVISOR, company_id=OTHER_COMPANY_ID)
    with pytest.raises(HTTPException) as exc:
        await svc.create_request(auth(), create_payload())
    assert exc.value.status_code == 400


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role,active",
    [(Rol.TECHNICIAN, True), (Rol.SUPERVISOR, False)],
)
async def test_creation_rejects_non_supervisor_or_inactive_supervisor(role, active):
    svc, repo, _ = service()
    repo.supervisor = user(SUPERVISOR_ID, role, active=active)
    with pytest.raises(HTTPException) as exc:
        await svc.create_request(auth(), create_payload())
    assert exc.value.status_code == 400


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "changes",
    [
        {"work_date": date(2026, 7, 5)},
        {"exit_time": time(6)},
    ],
)
async def test_creation_rejects_invalid_week_or_schedule(changes):
    svc, _, _ = service()
    with pytest.raises(HTTPException) as exc:
        await svc.create_request(auth(), create_payload(**changes))
    assert exc.value.status_code in {400, 422}


@pytest.mark.asyncio
async def test_technician_cannot_create_previous_sunday_when_clock_is_next_monday():
    monday_after_sunday = datetime(2026, 7, 13, 5, 0, tzinfo=timezone.utc)
    svc, _, _ = service(clock=lambda: monday_after_sunday)
    with pytest.raises(HTTPException) as exc:
        await svc.create_request(auth(), create_payload(work_date=date(2026, 7, 12)))
    assert exc.value.status_code == 400


def test_creation_schema_rejects_incomplete_break_pair():
    with pytest.raises(ValidationError, match="deben enviarse juntos"):
        create_payload(break_start_time=time(12), break_end_time=None)


def test_update_schema_rejects_empty_forbidden_and_null_nonnullable_fields():
    with pytest.raises(ValidationError, match="al menos un campo"):
        OvertimeRequestUpdate()
    with pytest.raises(ValidationError):
        OvertimeRequestUpdate(status="cancelled")
    with pytest.raises(ValidationError, match="no puede ser null"):
        OvertimeRequestUpdate(activity=None)


@pytest.mark.asyncio
async def test_technician_partially_edits_pending_request_and_creates_audit_event():
    svc, repo, db = service()
    submitted_at = repo.request.submitted_at
    created_at = repo.request.created_at

    result = await svc.update_own_request(
        auth(), repo.request.id,
        OvertimeRequestUpdate(exit_time=time(17), activity="Actividad actualizada"),
    )

    assert result.entry_time == time(7)
    assert result.exit_time == time(17)
    assert result.activity == "Actividad actualizada"
    assert (result.worked_minutes, result.regular_minutes, result.overtime_minutes) == (570, 480, 90)
    assert result.submitted_at == submitted_at
    assert result.created_at == created_at
    assert result.updated_at == NOW
    assert repo.overlap_kwargs["exclude_request_id"] == repo.request.id
    assert repo.lock_kwargs == {
        "request_id": repo.request.id,
        "company_id": COMPANY_ID,
        "technician_id": TECHNICIAN_ID,
    }
    event = repo.events[-1]
    assert event.event_type == OvertimeRequestEventType.EDITED
    assert event.previous_status == event.new_status == OvertimeRequestStatus.PENDING
    assert event.snapshot_before["exit_time"] == "16:30"
    assert event.snapshot_after["exit_time"] == "17:00"
    assert db.commit_calls == 0


@pytest.mark.asyncio
async def test_edit_can_remove_break_with_explicit_nulls():
    svc, repo, _ = service()
    result = await svc.update_own_request(
        auth(), repo.request.id,
        OvertimeRequestUpdate(break_start_time=None, break_end_time=None),
    )
    assert result.break_start_time is None
    assert result.break_end_time is None
    assert result.worked_minutes == 570


@pytest.mark.asyncio
async def test_edit_rejects_invalid_combined_break_without_event():
    svc, repo, _ = service()
    with pytest.raises(HTTPException) as exc:
        await svc.update_own_request(
            auth(), repo.request.id, OvertimeRequestUpdate(break_start_time=None)
        )
    assert exc.value.status_code == 400
    assert repo.events == []


@pytest.mark.asyncio
async def test_edit_revalidates_week_and_overlap_and_preserves_row_on_failure():
    svc, repo, _ = service()
    original = svc.snapshot(repo.request)
    with pytest.raises(HTTPException) as old_week:
        await svc.update_own_request(
            auth(), repo.request.id, OvertimeRequestUpdate(work_date=date(2026, 7, 5))
        )
    assert old_week.value.status_code == 400
    repo.overlap = True
    with pytest.raises(HTTPException) as overlap:
        await svc.update_own_request(
            auth(), repo.request.id, OvertimeRequestUpdate(entry_time=time(8))
        )
    assert overlap.value.status_code == 409
    assert repo.events == []
    assert original["work_date"] == "2026-07-08"


@pytest.mark.asyncio
async def test_edit_can_change_project_and_supervisor_and_updates_visibility_relation():
    svc, repo, _ = service()
    new_project = Proyecto(id=uuid4(), company_id=COMPANY_ID, nombre="Proyecto nuevo")
    new_supervisor = user(uuid4(), Rol.SUPERVISOR, uid="new-supervisor", name="Nuevo")
    repo.project = new_project
    repo.supervisor = new_supervisor
    result = await svc.update_own_request(
        auth(), repo.request.id,
        OvertimeRequestUpdate(
            project_id=new_project.id,
            authorizing_supervisor_id=new_supervisor.id,
        ),
    )
    assert result.project.id == new_project.id
    assert result.authorizing_supervisor.id == new_supervisor.id


@pytest.mark.asyncio
async def test_edit_accepts_all_mutable_fields_and_recalculates_final_object():
    svc, repo, _ = service()
    result = await svc.update_own_request(
        auth(), repo.request.id,
        OvertimeRequestUpdate(
            work_date=date(2026, 7, 9),
            entry_time=time(8),
            break_start_time=None,
            break_end_time=None,
            exit_time=time(18),
            activity="Todos los campos editados",
            project_id=PROJECT_ID,
            authorizing_supervisor_id=SUPERVISOR_ID,
        ),
    )
    assert result.work_date == date(2026, 7, 9)
    assert result.entry_time == time(8)
    assert result.exit_time == time(18)
    assert result.break_start_time is result.break_end_time is None
    assert (result.worked_minutes, result.regular_minutes, result.overtime_minutes) == (600, 480, 120)


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid", ["project", "supervisor"])
async def test_edit_rejects_invalid_final_project_or_supervisor(invalid):
    svc, repo, _ = service()
    if invalid == "project":
        repo.project = Proyecto(id=PROJECT_ID, company_id=OTHER_COMPANY_ID, nombre="Otro")
        payload = OvertimeRequestUpdate(project_id=PROJECT_ID)
    else:
        repo.supervisor = user(SUPERVISOR_ID, Rol.SUPERVISOR, company_id=OTHER_COMPANY_ID)
        payload = OvertimeRequestUpdate(authorizing_supervisor_id=SUPERVISOR_ID)
    with pytest.raises(HTTPException) as exc:
        await svc.update_own_request(auth(), repo.request.id, payload)
    assert exc.value.status_code == 400
    assert repo.events == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        OvertimeRequestStatus.APPROVED,
        OvertimeRequestStatus.ADJUSTED,
        OvertimeRequestStatus.REJECTED,
        OvertimeRequestStatus.CANCELLED,
    ],
)
async def test_edit_and_cancel_reject_non_pending_owned_request(status):
    svc, repo, _ = service()
    repo.request.status = status
    with pytest.raises(HTTPException) as edit:
        await svc.update_own_request(auth(), repo.request.id, OvertimeRequestUpdate(activity="Cambio"))
    with pytest.raises(HTTPException) as cancel:
        await svc.cancel_own_request(auth(), repo.request.id)
    assert edit.value.status_code == cancel.value.status_code == 409


@pytest.mark.asyncio
async def test_edit_and_cancel_hide_unowned_request_with_404():
    svc, repo, _ = service()
    repo.request = None
    with pytest.raises(HTTPException) as edit:
        await svc.update_own_request(auth(), uuid4(), OvertimeRequestUpdate(activity="Cambio"))
    with pytest.raises(HTTPException) as cancel:
        await svc.cancel_own_request(auth(), uuid4())
    assert edit.value.status_code == cancel.value.status_code == 404


@pytest.mark.asyncio
async def test_technician_cancels_pending_request_without_review_fields_or_data_loss():
    svc, repo, db = service()
    original = svc.snapshot(repo.request)
    result = await svc.cancel_own_request(auth(), repo.request.id)
    assert result.status == OvertimeRequestStatus.CANCELLED
    assert result.entry_time == time(7)
    assert result.reviewed_at is None
    assert repo.request.reviewed_by_user_id is None
    assert repo.request.supervisor_note is None
    event = repo.events[-1]
    assert event.event_type == OvertimeRequestEventType.CANCELLED
    assert event.previous_status == OvertimeRequestStatus.PENDING
    assert event.new_status == OvertimeRequestStatus.CANCELLED
    assert event.snapshot_before["status"] == original["status"] == "pending"
    assert event.snapshot_after["status"] == "cancelled"
    assert db.commit_calls == 0


@pytest.mark.asyncio
async def test_catalogs_only_return_safe_same_company_fields():
    svc, _, _ = service()
    projects = await svc.list_project_catalog(auth())
    supervisors = await svc.list_supervisor_catalog(auth())
    assert projects[0].model_dump() == {"id": PROJECT_ID, "name": "Proyecto activo"}
    assert supervisors[0].model_dump() == {"id": SUPERVISOR_ID, "name": "Supervisor"}


@pytest.mark.asyncio
async def test_supervisor_technician_catalog_uses_internal_ids_and_resolved_company():
    svc, repo, _ = service()
    second = user(uuid4(), Rol.TECHNICIAN, uid="firebase-other", name="Álvaro")
    repo.technicians = [second, TECHNICIAN]
    result = await svc.list_technician_catalog_for_supervisor(auth("supervisor-uid"))
    assert [item.model_dump() for item in result] == [
        {"id": second.id, "name": "Álvaro"},
        {"id": TECHNICIAN_ID, "name": "Técnico"},
    ]
    assert repo.list_kwargs == {"company_id": COMPANY_ID}
    assert all(str(item.id) not in {user.uid for user in repo.technicians} for item in result)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "resolved_user",
    [None, user(SUPERVISOR_ID, Rol.SUPERVISOR, active=False), TECHNICIAN],
)
async def test_supervisor_technician_catalog_rejects_missing_inactive_or_wrong_role(resolved_user):
    svc, repo, _ = service()
    repo.users["supervisor-uid"] = resolved_user
    with pytest.raises(HTTPException) as exc:
        await svc.list_technician_catalog_for_supervisor(auth("supervisor-uid"))
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_technician_queries_are_scoped_to_resolved_identity_and_company():
    svc, repo, _ = service()
    await svc.list_own_requests(auth(), status=None, date_from=None, date_to=None, skip=0, limit=20)
    assert repo.list_kwargs["company_id"] == COMPANY_ID
    assert repo.list_kwargs["technician_id"] == TECHNICIAN_ID


@pytest.mark.asyncio
async def test_technician_page_applies_panama_default_range_and_metadata():
    svc, repo, _ = service()
    result = await svc.page_own_requests(
        auth(), status=None, date_from=None, date_to=None, page=1, page_size=20
    )
    assert result.model_dump() == {
        "items": [svc.to_summary(repo.request).model_dump()],
        "page": 1,
        "page_size": 20,
        "total": 1,
        "total_pages": 1,
        "date_from": date(2026, 6, 8),
        "date_to": date(2026, 7, 8),
    }
    assert repo.list_kwargs["company_id"] == COMPANY_ID
    assert repo.list_kwargs["technician_id"] == TECHNICIAN_ID
    assert repo.list_kwargs["offset"] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "date_from,date_to,expected",
    [
        (date(2026, 6, 1), None, (date(2026, 6, 1), date(2026, 7, 1))),
        (None, date(2026, 7, 1), (date(2026, 6, 1), date(2026, 7, 1))),
        (date(2025, 7, 12), date(2026, 7, 12), (date(2025, 7, 12), date(2026, 7, 12))),
    ],
)
async def test_page_date_range_normalization_allows_366_days(date_from, date_to, expected):
    svc, repo, _ = service()
    await svc.page_own_requests(
        auth(), status=OvertimeRequestStatus.CANCELLED,
        date_from=date_from, date_to=date_to, page=3, page_size=10,
    )
    assert (repo.list_kwargs["date_from"], repo.list_kwargs["date_to"]) == expected
    assert repo.list_kwargs["status"] == OvertimeRequestStatus.CANCELLED
    assert repo.list_kwargs["offset"] == 20


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "date_from,date_to",
    [
        (date(2026, 7, 2), date(2026, 7, 1)),
        (date(2025, 7, 11), date(2026, 7, 12)),
    ],
)
async def test_page_rejects_inverted_or_367_day_range(date_from, date_to):
    svc, _, _ = service()
    with pytest.raises(HTTPException) as exc:
        await svc.page_own_requests(
            auth(), status=None, date_from=date_from, date_to=date_to, page=1, page_size=20
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_page_out_of_range_is_empty_and_preserves_metadata():
    svc, repo, _ = service()
    repo.page_rows = []
    repo.page_total = 21
    result = await svc.page_own_requests(
        auth(), status=None, date_from=date(2026, 6, 1), date_to=date(2026, 6, 30),
        page=4, page_size=10,
    )
    assert result.items == []
    assert result.total == 21
    assert result.total_pages == 3


@pytest.mark.asyncio
async def test_supervisor_page_is_scoped_to_assignment_company_and_optional_technician():
    svc, repo, _ = service()
    await svc.page_assigned_requests(
        auth("supervisor-uid"), status=OvertimeRequestStatus.PENDING,
        technician_id=TECHNICIAN_ID, date_from=date(2026, 6, 1),
        date_to=date(2026, 6, 30), page=2, page_size=5,
    )
    assert repo.list_kwargs["company_id"] == COMPANY_ID
    assert repo.list_kwargs["supervisor_id"] == SUPERVISOR_ID
    assert repo.list_kwargs["technician_id"] == TECHNICIAN_ID
    assert repo.list_kwargs["offset"] == 5


@pytest.mark.asyncio
async def test_pdf_export_uses_full_filtered_result_and_builds_authoritative_totals():
    repo = FakeRepository()
    second = pending_request()
    second.id = uuid4()
    second.break_start_time = None
    second.break_end_time = None
    second.status = OvertimeRequestStatus.CANCELLED
    second.worked_minutes = 1500
    second.regular_minutes = 480
    second.overtime_minutes = 1020
    second.activity = "<script>alert('x')</script>"
    repo.export_rows = [repo.request, second]
    repo.export_total = 2
    renderer = FakePdfRenderer()
    svc = OvertimeRequestService(
        FakeDB(), repository=repo, clock=lambda: NOW, pdf_renderer=renderer
    )

    pdf, effective_from, effective_to = await svc.export_assigned_requests_pdf(
        auth("supervisor-uid"), status=None, technician_id=None,
        date_from=None, date_to=None,
    )

    assert pdf.startswith(b"%PDF")
    assert (effective_from, effective_to) == (date(2026, 6, 8), date(2026, 7, 8))
    assert repo.list_kwargs["company_id"] == COMPANY_ID
    assert repo.list_kwargs["supervisor_id"] == SUPERVISOR_ID
    assert renderer.context["rows"][1]["break_time"] == "No aplica"
    assert renderer.context["rows"][1]["status"] == "Cancelada"
    assert renderer.context["rows"][1]["worked"] == "25:00"
    assert renderer.context["grand_total"] == {
        "count": 2, "worked": "34:00", "regular": "16:00", "overtime": "18:00",
        "worked_minutes": 2040, "regular_minutes": 960, "overtime_minutes": 1080,
    }
    assert renderer.context["technician_totals"][0]["count"] == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("total,allowed", [(2000, True), (2001, False)])
async def test_pdf_export_enforces_volume_before_querying_rows_or_rendering(total, allowed):
    repo = FakeRepository()
    repo.export_total = total
    repo.export_rows = []
    renderer = FakePdfRenderer()
    svc = OvertimeRequestService(
        FakeDB(), repository=repo, clock=lambda: NOW, pdf_renderer=renderer
    )
    if allowed:
        await svc.export_assigned_requests_pdf(
            auth("supervisor-uid"), status=None, technician_id=None,
            date_from=date(2026, 7, 1), date_to=date(2026, 7, 8),
        )
        assert repo.export_list_calls == renderer.calls == 1
    else:
        with pytest.raises(HTTPException) as exc:
            await svc.export_assigned_requests_pdf(
                auth("supervisor-uid"), status=None, technician_id=None,
                date_from=date(2026, 7, 1), date_to=date(2026, 7, 8),
            )
        assert exc.value.status_code == 413
        assert "2000 solicitudes" in exc.value.detail
        assert repo.export_list_calls == renderer.calls == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("total,allowed", [(10000, True), (10001, False)])
async def test_xlsx_export_enforces_its_volume_before_querying_or_rendering(total, allowed):
    repo = FakeRepository()
    repo.export_total = total
    repo.export_rows = []
    renderer = FakeXlsxRenderer()
    svc = OvertimeRequestService(
        FakeDB(), repository=repo, clock=lambda: NOW, xlsx_renderer=renderer
    )
    if allowed:
        content, media_type, filename = await svc.export_assigned_requests(
            auth("supervisor-uid"), export_format="xlsx", status=None, technician_id=None,
            date_from=date(2026, 7, 1), date_to=date(2026, 7, 8),
        )
        assert content.startswith(b"PK")
        assert media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert filename == "horas-extra_2026-07-01_2026-07-08.xlsx"
        assert repo.export_list_calls == renderer.calls == 1
    else:
        with pytest.raises(HTTPException) as exc:
            await svc.export_assigned_requests(
                auth("supervisor-uid"), export_format="xlsx", status=None,
                technician_id=None, date_from=date(2026, 7, 1), date_to=date(2026, 7, 8),
            )
        assert exc.value.status_code == 413
        assert exc.value.detail == (
            "El reporte supera el máximo de 10000 solicitudes para XLSX. "
            "Reduce el período o aplica más filtros."
        )
        assert repo.export_list_calls == renderer.calls == 0
    await svc.get_own_request(auth(), repo.request.id)
    assert repo.list_kwargs["company_id"] == COMPANY_ID
    assert repo.list_kwargs["technician_id"] == TECHNICIAN_ID


@pytest.mark.asyncio
async def test_hidden_technician_request_returns_404():
    svc, repo, _ = service()
    repo.request = None
    with pytest.raises(HTTPException) as exc:
        await svc.get_own_request(auth(), uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_supervisor_queries_are_scoped_to_assignment_and_company():
    svc, repo, _ = service()
    await svc.list_assigned_requests(
        auth("supervisor-uid"), status=None, technician_id=None,
        date_from=None, date_to=None, skip=0, limit=20
    )
    assert repo.list_kwargs["company_id"] == COMPANY_ID
    assert repo.list_kwargs["supervisor_id"] == SUPERVISOR_ID


@pytest.mark.asyncio
async def test_hidden_supervisor_request_returns_404():
    svc, repo, _ = service()
    repo.request = None
    with pytest.raises(HTTPException) as exc:
        await svc.get_assigned_request(auth("supervisor-uid"), uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_assigned_supervisor_approves_and_preserves_work_data():
    svc, repo, db = service()
    original = svc.snapshot(repo.request)
    result = await svc.approve(auth("supervisor-uid"), repo.request.id, OvertimeApproveRequest(note=None))
    assert result.status == OvertimeRequestStatus.APPROVED
    assert result.entry_time == time(7)
    assert result.activity == "Actividad original"
    assert repo.events[-1].event_type == OvertimeRequestEventType.APPROVED
    assert repo.events[-1].snapshot_before["entry_time"] == original["entry_time"]
    assert db.commit_calls == 0
    assert repo.lock_kwargs["supervisor_id"] == SUPERVISOR_ID


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["approve", "adjust", "reject"])
async def test_second_review_attempt_returns_409(action):
    svc, repo, _ = service()
    repo.request.status = OvertimeRequestStatus.APPROVED
    with pytest.raises(HTTPException) as exc:
        if action == "approve":
            await svc.approve(auth("supervisor-uid"), repo.request.id, OvertimeApproveRequest())
        elif action == "reject":
            await svc.reject(auth("supervisor-uid"), repo.request.id, OvertimeRejectRequest(note="Motivo"))
        else:
            await svc.adjust_and_approve(
                auth("supervisor-uid"), repo.request.id,
                OvertimeAdjustAndApproveRequest(
                    entry_time=time(7), break_start_time=time(12), break_end_time=time(12, 30),
                    exit_time=time(17), activity="Ajustada", project_id=PROJECT_ID, note="Corrección"
                ),
            )
    assert exc.value.status_code == 409


@pytest.mark.parametrize("schema", [OvertimeRejectRequest, OvertimeAdjustAndApproveRequest])
def test_required_review_note_rejects_whitespace(schema):
    data = {"note": "   "}
    if schema is OvertimeAdjustAndApproveRequest:
        data.update(
            entry_time=time(7), break_start_time=None, break_end_time=None,
            exit_time=time(17), activity="Actividad", project_id=PROJECT_ID
        )
    with pytest.raises(ValidationError):
        schema(**data)


@pytest.mark.asyncio
async def test_adjustment_recalculates_and_creates_before_after_snapshots_without_identity_changes():
    svc, repo, _ = service()
    payload = OvertimeAdjustAndApproveRequest(
        entry_time=time(7), break_start_time=time(12), break_end_time=time(12, 30),
        exit_time=time(17), activity="Actividad corregida", project_id=PROJECT_ID,
        note="Se corrigió la salida",
    )
    result = await svc.adjust_and_approve(auth("supervisor-uid"), repo.request.id, payload)
    assert result.status == OvertimeRequestStatus.ADJUSTED
    assert (result.worked_minutes, result.regular_minutes, result.overtime_minutes) == (570, 480, 90)
    assert repo.request.technician_id == TECHNICIAN_ID
    assert repo.request.authorizing_supervisor_id == SUPERVISOR_ID
    event = repo.events[-1]
    assert event.event_type == OvertimeRequestEventType.ADJUSTED_AND_APPROVED
    assert event.snapshot_before["exit_time"] == "16:30"
    assert event.snapshot_after["exit_time"] == "17:00"


@pytest.mark.asyncio
async def test_adjustment_translates_database_overlap_violation_to_409():
    svc, repo, _ = service()
    repo.fail_event = integrity_error(OvertimeRequestService.ACTIVE_OVERLAP_CONSTRAINT)
    payload = OvertimeAdjustAndApproveRequest(
        entry_time=time(7), break_start_time=None, break_end_time=None,
        exit_time=time(17), activity="Actividad corregida", project_id=PROJECT_ID,
        note="Corrección",
    )

    with pytest.raises(HTTPException) as exc:
        await svc.adjust_and_approve(auth("supervisor-uid"), repo.request.id, payload)

    assert exc.value.status_code == 409
    assert exc.value.detail == OvertimeRequestService.ACTIVE_OVERLAP_DETAIL


@pytest.mark.asyncio
async def test_supervisor_can_adjust_and_approve_previous_sunday_on_next_monday():
    monday_after_sunday = datetime(2026, 7, 13, 5, 0, tzinfo=timezone.utc)
    svc, repo, _ = service(clock=lambda: monday_after_sunday)
    repo.request.work_date = date(2026, 7, 12)
    payload = OvertimeAdjustAndApproveRequest(
        entry_time=time(7), break_start_time=time(12), break_end_time=time(12, 30),
        exit_time=time(18, 30), activity="Actividad corregida", project_id=PROJECT_ID,
        note="Corrección posterior",
    )

    result = await svc.adjust_and_approve(auth("supervisor-uid"), repo.request.id, payload)

    assert result.status == OvertimeRequestStatus.ADJUSTED
    assert result.work_date == date(2026, 7, 12)
    assert (result.worked_minutes, result.regular_minutes, result.overtime_minutes) == (660, 480, 180)
    event = repo.events[-1]
    assert event.event_type == OvertimeRequestEventType.ADJUSTED_AND_APPROVED
    assert event.snapshot_after["worked_minutes"] == 660
    assert event.snapshot_after["regular_minutes"] == 480
    assert event.snapshot_after["overtime_minutes"] == 180


@pytest.mark.asyncio
async def test_adjustment_rejects_project_from_other_company():
    svc, repo, _ = service()
    repo.project = Proyecto(id=PROJECT_ID, company_id=OTHER_COMPANY_ID, nombre="Otro")
    with pytest.raises(HTTPException) as exc:
        await svc.adjust_and_approve(
            auth("supervisor-uid"), repo.request.id,
            OvertimeAdjustAndApproveRequest(
                entry_time=time(7), break_start_time=None, break_end_time=None,
                exit_time=time(17), activity="Actividad", project_id=PROJECT_ID, note="Motivo"
            ),
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_rejection_preserves_schedule_and_creates_rejected_event():
    svc, repo, _ = service()
    original = svc.snapshot(repo.request)
    result = await svc.reject(
        auth("supervisor-uid"), repo.request.id, OvertimeRejectRequest(note="No coincide")
    )
    assert result.status == OvertimeRequestStatus.REJECTED
    assert result.entry_time == time(7)
    assert repo.events[-1].event_type == OvertimeRequestEventType.REJECTED
    assert repo.events[-1].snapshot_before["entry_time"] == original["entry_time"]


@pytest.mark.asyncio
async def test_event_failure_propagates_and_service_does_not_commit():
    svc, repo, db = service()
    repo.fail_event = True
    with pytest.raises(RuntimeError, match="audit failed"):
        await svc.approve(auth("supervisor-uid"), repo.request.id, OvertimeApproveRequest())
    assert db.commit_calls == 0


def test_snapshot_is_json_serializable_primitives():
    snapshot = OvertimeRequestService.snapshot(pending_request())
    assert snapshot["id"] and isinstance(snapshot["id"], str)
    assert snapshot["work_date"] == "2026-07-08"
    assert snapshot["entry_time"] == "07:00"
    assert snapshot["status"] == "pending"
