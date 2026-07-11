from datetime import date, datetime, time, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.db.models.overtime_requests import OvertimeRequest, OvertimeRequestEventType, OvertimeRequestStatus
from app.db.models.proyectos import Proyecto
from app.db.models.usuarios import Rol, Usuario
from app.schemas.overtime_requests import (
    OvertimeAdjustAndApproveRequest,
    OvertimeApproveRequest,
    OvertimeRejectRequest,
    OvertimeRequestCreate,
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
        self.request = pending_request()
        self.events = []
        self.created_requests = []
        self.fail_event = False
        self.list_kwargs = None
        self.lock_kwargs = None

    async def get_user_by_uid(self, uid):
        return self.users.get(uid)

    async def list_active_projects(self, company_id):
        return [self.project] if self.project and self.project.company_id == company_id else []

    async def list_active_supervisors(self, company_id):
        return [self.supervisor] if self.supervisor and self.supervisor.company_id == company_id else []

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
        request.id = request.id or uuid4()
        self.created_requests.append(request)
        return request

    async def create_event(self, event):
        if self.fail_event:
            raise RuntimeError("audit failed")
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


def service(repo=None, clock=None):
    repository = repo or FakeRepository()
    db = FakeDB()
    return OvertimeRequestService(db, repository=repository, clock=clock or (lambda: NOW)), repository, db


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


@pytest.mark.asyncio
async def test_catalogs_only_return_safe_same_company_fields():
    svc, _, _ = service()
    projects = await svc.list_project_catalog(auth())
    supervisors = await svc.list_supervisor_catalog(auth())
    assert projects[0].model_dump() == {"id": PROJECT_ID, "name": "Proyecto activo"}
    assert supervisors[0].model_dump() == {"id": SUPERVISOR_ID, "name": "Supervisor"}


@pytest.mark.asyncio
async def test_technician_queries_are_scoped_to_resolved_identity_and_company():
    svc, repo, _ = service()
    await svc.list_own_requests(auth(), status=None, date_from=None, date_to=None, skip=0, limit=20)
    assert repo.list_kwargs["company_id"] == COMPANY_ID
    assert repo.list_kwargs["technician_id"] == TECHNICIAN_ID
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
