from datetime import date, datetime, timezone
from types import SimpleNamespace
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.api.routes import overtime_requests
from app.auth.firebase import get_current_firebase_user
from app.db.session import get_db


COMPANY_ID = UUID("11111111-1111-1111-1111-111111111111")
PROJECT_ID = UUID("55555555-5555-5555-5555-555555555555")
SUPERVISOR_ID = UUID("44444444-4444-4444-4444-444444444444")
REQUEST_ID = UUID("66666666-6666-6666-6666-666666666666")
NOW = datetime(2026, 7, 8, 15, 0, tzinfo=timezone.utc)


def detail(status="pending"):
    return {
        "id": REQUEST_ID,
        "work_date": date(2026, 7, 8),
        "entry_time": "07:00",
        "break_start_time": "12:00",
        "break_end_time": "12:30",
        "exit_time": "16:30",
        "activity": "Mantenimiento",
        "project": {"id": PROJECT_ID, "name": "Proyecto"},
        "technician": {"id": UUID("33333333-3333-3333-3333-333333333333"), "name": "Técnico"},
        "authorizing_supervisor": {"id": SUPERVISOR_ID, "name": "Supervisor"},
        "worked_minutes": 540,
        "regular_minutes": 480,
        "overtime_minutes": 60,
        "status": status,
        "supervisor_note": None,
        "submitted_at": NOW,
        "reviewed_at": None,
        "created_at": NOW,
        "updated_at": NOW,
        "events": [],
    }


class FakeOvertimeService:
    calls = []

    def __init__(self, db):
        self.db = db

    async def list_project_catalog(self, current_user):
        return [{"id": PROJECT_ID, "name": "Proyecto"}]

    async def list_supervisor_catalog(self, current_user):
        return [{"id": SUPERVISOR_ID, "name": "Supervisor"}]

    async def create_request(self, current_user, payload):
        self.calls.append(("create", payload.model_dump()))
        return detail()

    async def list_own_requests(self, current_user, **kwargs):
        self.calls.append(("list-own", kwargs))
        return []

    async def get_own_request(self, current_user, request_id):
        return detail()

    async def list_assigned_requests(self, current_user, **kwargs):
        self.calls.append(("list-supervisor", kwargs))
        return []

    async def get_assigned_request(self, current_user, request_id):
        return detail()

    async def approve(self, current_user, request_id, payload):
        return detail("approved")

    async def adjust_and_approve(self, current_user, request_id, payload):
        return detail("adjusted")

    async def reject(self, current_user, request_id, payload):
        return detail("rejected")


def create_app(monkeypatch, role):
    FakeOvertimeService.calls = []
    monkeypatch.setattr(overtime_requests, "OvertimeRequestService", FakeOvertimeService)
    app = FastAPI()
    app.include_router(overtime_requests.router, prefix="/api/overtime")

    async def fake_db():
        yield SimpleNamespace()

    async def fake_auth(request: Request):
        current_user = SimpleNamespace(uid=f"{role}-uid", rol=role, company_id=COMPANY_ID)
        request.state.current_user = current_user
        return current_user

    app.dependency_overrides[get_db] = fake_db
    app.dependency_overrides[get_current_firebase_user] = fake_auth
    for route in app.routes:
        dependant = getattr(route, "dependant", None)
        if dependant:
            for dependency in dependant.dependencies:
                if getattr(dependency.call, "__name__", "") == "role_dependency":
                    app.dependency_overrides[dependency.call] = fake_auth
    return app


def test_technician_catalogs_expose_only_id_and_name(monkeypatch):
    client = TestClient(create_app(monkeypatch, "technician"))
    assert client.get("/api/overtime/catalogs/projects").json() == [
        {"id": str(PROJECT_ID), "name": "Proyecto"}
    ]
    assert client.get("/api/overtime/catalogs/supervisors").json() == [
        {"id": str(SUPERVISOR_ID), "name": "Supervisor"}
    ]


def test_create_contract_returns_201_and_rejects_calculated_fields(monkeypatch):
    client = TestClient(create_app(monkeypatch, "technician"))
    payload = {
        "work_date": "2026-07-08", "entry_time": "07:00",
        "break_start_time": "12:00", "break_end_time": "12:30",
        "exit_time": "16:30", "activity": "Mantenimiento",
        "project_id": str(PROJECT_ID), "authorizing_supervisor_id": str(SUPERVISOR_ID),
    }
    response = client.post("/api/overtime/requests", json=payload)
    assert response.status_code == 201
    assert response.json()["worked_minutes"] == 540
    response = client.post("/api/overtime/requests", json={**payload, "worked_minutes": 1})
    assert response.status_code == 422


def test_list_filters_are_typed_and_forwarded(monkeypatch):
    client = TestClient(create_app(monkeypatch, "technician"))
    response = client.get(
        "/api/overtime/requests/me",
        params={"status": "pending", "date_from": "2026-07-06", "date_to": "2026-07-12", "skip": 2, "limit": 10},
    )
    assert response.status_code == 200
    filters = FakeOvertimeService.calls[-1][1]
    assert filters["status"].value == "pending"
    assert filters["date_from"] == date(2026, 7, 6)
    assert filters["skip"] == 2 and filters["limit"] == 10


def test_supervisor_transition_contracts(monkeypatch):
    client = TestClient(create_app(monkeypatch, "supervisor"))
    assert client.post(f"/api/overtime/supervisor/requests/{REQUEST_ID}/approve", json={}).status_code == 200
    assert client.post(
        f"/api/overtime/supervisor/requests/{REQUEST_ID}/reject", json={"note": "   "}
    ).status_code == 422
    adjustment = {
        "entry_time": "07:00", "break_start_time": None, "break_end_time": None,
        "exit_time": "17:00", "activity": "Corregida", "project_id": str(PROJECT_ID),
        "note": "Corrección validada",
    }
    response = client.post(
        f"/api/overtime/supervisor/requests/{REQUEST_ID}/adjust-and-approve", json=adjustment
    )
    assert response.status_code == 200
    assert response.json()["status"] == "adjusted"


def test_overtime_router_has_no_edit_or_delete_endpoints():
    methods_and_paths = {
        (method, route.path)
        for route in overtime_requests.router.routes
        for method in route.methods
    }
    assert not any(method in {"PUT", "PATCH", "DELETE"} for method, _ in methods_and_paths)
    assert ("POST", "/requests") in methods_and_paths
    assert ("POST", "/supervisor/requests/{request_id}/reject") in methods_and_paths
