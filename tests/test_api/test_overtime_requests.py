from datetime import date, datetime, timezone
from types import SimpleNamespace
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi import HTTPException
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

    async def list_technician_catalog_for_supervisor(self, current_user):
        return [{"id": REQUEST_ID, "name": "Técnico"}]

    async def create_request(self, current_user, payload):
        self.calls.append(("create", payload.model_dump()))
        return detail()

    async def list_own_requests(self, current_user, **kwargs):
        self.calls.append(("list-own", kwargs))
        return []

    async def page_own_requests(self, current_user, **kwargs):
        self.calls.append(("page-own", kwargs))
        return {
            "items": [], "page": kwargs["page"], "page_size": kwargs["page_size"],
            "total": 0, "total_pages": 0,
            "date_from": kwargs["date_from"] or date(2026, 6, 12),
            "date_to": kwargs["date_to"] or date(2026, 7, 12),
        }

    async def get_own_request(self, current_user, request_id):
        return detail()

    async def update_own_request(self, current_user, request_id, payload):
        self.calls.append(("update-own", payload.model_dump(exclude_unset=True)))
        return detail()

    async def cancel_own_request(self, current_user, request_id):
        self.calls.append(("cancel-own", request_id))
        return detail("cancelled")

    async def list_assigned_requests(self, current_user, **kwargs):
        self.calls.append(("list-supervisor", kwargs))
        return []

    async def page_assigned_requests(self, current_user, **kwargs):
        self.calls.append(("page-supervisor", kwargs))
        return {
            "items": [], "page": kwargs["page"], "page_size": kwargs["page_size"],
            "total": 0, "total_pages": 0,
            "date_from": kwargs["date_from"] or date(2026, 6, 12),
            "date_to": kwargs["date_to"] or date(2026, 7, 12),
        }

    async def export_assigned_requests(self, current_user, **kwargs):
        self.calls.append(("export-supervisor", kwargs))
        export_format = kwargs["export_format"]
        if export_format == "pdf":
            return b"%PDF-fake", "application/pdf", "horas-extra_2026-06-12_2026-07-12.pdf"
        return (
            b"PK\x03\x04-xlsx-fake",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "horas-extra_2026-06-12_2026-07-12.xlsx",
        )

    async def get_assigned_request(self, current_user, request_id):
        return detail()

    async def approve(self, current_user, request_id, payload):
        return detail("approved")

    async def adjust_and_approve(self, current_user, request_id, payload):
        return detail("adjusted")

    async def reject(self, current_user, request_id, payload):
        return detail("rejected")


def create_app(monkeypatch, role, *, enforce_role=False):
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
    if not enforce_role:
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


def test_supervisor_technician_catalog_exposes_postgresql_uuid_and_exact_shape(monkeypatch):
    client = TestClient(create_app(monkeypatch, "supervisor"))
    response = client.get("/api/overtime/supervisor/catalogs/technicians")
    assert response.status_code == 200
    assert response.json() == [{"id": str(REQUEST_ID), "name": "Técnico"}]


def test_supervisor_technician_catalog_rejects_technician_role(monkeypatch):
    client = TestClient(create_app(monkeypatch, "technician", enforce_role=True))
    assert client.get("/api/overtime/supervisor/catalogs/technicians").status_code == 403


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


def test_create_contract_exposes_stable_overlap_conflict(monkeypatch):
    app = create_app(monkeypatch, "technician")

    async def conflict(self, current_user, payload):
        raise HTTPException(
            status_code=409,
            detail="Ya existe una solicitud activa que se solapa con la fecha y el horario indicados.",
        )

    monkeypatch.setattr(FakeOvertimeService, "create_request", conflict)
    response = TestClient(app).post(
        "/api/overtime/requests",
        json={
            "work_date": "2026-07-08",
            "entry_time": "07:00",
            "break_start_time": None,
            "break_end_time": None,
            "exit_time": "10:00",
            "activity": "Mantenimiento",
            "project_id": str(PROJECT_ID),
            "authorizing_supervisor_id": str(SUPERVISOR_ID),
        },
    )
    assert response.status_code == 409
    assert response.json() == {
        "detail": "Ya existe una solicitud activa que se solapa con la fecha y el horario indicados."
    }


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


def test_legacy_lists_remain_arrays_and_page_routes_have_exact_shape(monkeypatch):
    technician = TestClient(create_app(monkeypatch, "technician"))
    assert technician.get("/api/overtime/requests/me").json() == []
    response = technician.get("/api/overtime/requests/me/page")
    assert response.status_code == 200
    assert response.json() == {
        "items": [], "page": 1, "page_size": 20, "total": 0, "total_pages": 0,
        "date_from": "2026-06-12", "date_to": "2026-07-12",
    }
    assert technician.get("/api/overtime/requests/me/page", params={"page": 0}).status_code == 422
    assert technician.get(
        "/api/overtime/requests/me/page", params={"page_size": 101}
    ).status_code == 422


def test_supervisor_page_forwards_filters_without_expanding_visibility(monkeypatch):
    client = TestClient(create_app(monkeypatch, "supervisor"))
    response = client.get(
        "/api/overtime/supervisor/requests/page",
        params={
            "status": "cancelled", "technician_id": str(REQUEST_ID),
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "page": 2, "page_size": 5,
        },
    )
    assert response.status_code == 200
    call, filters = FakeOvertimeService.calls[-1]
    assert call == "page-supervisor"
    assert filters["status"].value == "cancelled"
    assert filters["technician_id"] == REQUEST_ID
    assert filters["page"] == 2 and filters["page_size"] == 5


def test_technician_page_does_not_declare_technician_filter_and_page_is_not_uuid(monkeypatch):
    client = TestClient(create_app(monkeypatch, "technician"))
    assert client.get("/api/overtime/requests/me/page").status_code == 200
    route = next(
        route for route in overtime_requests.router.routes
        if route.path == "/requests/me/page"
    )
    assert "technician_id" not in {parameter.name for parameter in route.dependant.query_params}


def test_supervisor_pdf_export_contract_returns_binary_attachment(monkeypatch):
    client = TestClient(create_app(monkeypatch, "supervisor"))
    response = client.get(
        "/api/overtime/supervisor/requests/export",
        params={"format": "pdf", "status": "cancelled"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == (
        'attachment; filename="horas-extra_2026-06-12_2026-07-12.pdf"'
    )
    assert response.content.startswith(b"%PDF")
    assert FakeOvertimeService.calls[-1][0] == "export-supervisor"


def test_pdf_export_requires_supported_format_and_is_not_captured_as_uuid(monkeypatch):
    client = TestClient(create_app(monkeypatch, "supervisor"))
    path = "/api/overtime/supervisor/requests/export"
    assert client.get(path).status_code == 422
    assert client.get(path, params={"format": "csv"}).status_code == 422
    assert client.get(path, params={"format": "pdf"}).status_code == 200


def test_supervisor_xlsx_export_contract_returns_binary_attachment(monkeypatch):
    client = TestClient(create_app(monkeypatch, "supervisor"))
    response = client.get(
        "/api/overtime/supervisor/requests/export", params={"format": "xlsx"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert response.headers["content-disposition"] == (
        'attachment; filename="horas-extra_2026-06-12_2026-07-12.xlsx"'
    )
    assert response.content.startswith(b"PK")


def test_xlsx_export_rejects_technician_role(monkeypatch):
    client = TestClient(create_app(monkeypatch, "technician", enforce_role=True))
    response = client.get(
        "/api/overtime/supervisor/requests/export", params={"format": "xlsx"}
    )
    assert response.status_code == 403


def test_openapi_exposes_consolidated_overtime_contract_and_binary_export(monkeypatch):
    app = create_app(monkeypatch, "supervisor")
    schema = app.openapi()
    expected = {
        ("get", "/api/overtime/catalogs/projects"),
        ("get", "/api/overtime/catalogs/supervisors"),
        ("get", "/api/overtime/supervisor/catalogs/technicians"),
        ("post", "/api/overtime/requests"),
        ("get", "/api/overtime/requests/me"),
        ("get", "/api/overtime/requests/me/page"),
        ("get", "/api/overtime/requests/me/{request_id}"),
        ("patch", "/api/overtime/requests/me/{request_id}"),
        ("post", "/api/overtime/requests/me/{request_id}/cancel"),
        ("get", "/api/overtime/supervisor/requests"),
        ("get", "/api/overtime/supervisor/requests/page"),
        ("get", "/api/overtime/supervisor/requests/export"),
        ("get", "/api/overtime/supervisor/requests/{request_id}"),
        ("post", "/api/overtime/supervisor/requests/{request_id}/approve"),
        ("post", "/api/overtime/supervisor/requests/{request_id}/adjust-and-approve"),
        ("post", "/api/overtime/supervisor/requests/{request_id}/reject"),
    }
    actual = {
        (method, path)
        for path, operations in schema["paths"].items()
        for method in operations
        if method in {"get", "post", "patch"}
    }
    assert actual == expected

    export = schema["paths"]["/api/overtime/supervisor/requests/export"]["get"]
    format_parameter = next(item for item in export["parameters"] if item["name"] == "format")
    assert format_parameter["required"] is True
    assert format_parameter["schema"]["enum"] == ["pdf", "xlsx"]
    assert set(export["responses"]["200"]["content"]) == {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    catalog = schema["paths"]["/api/overtime/supervisor/catalogs/technicians"]["get"]
    catalog_items = catalog["responses"]["200"]["content"]["application/json"]["schema"]
    assert catalog_items == {
        "items": {"$ref": "#/components/schemas/OvertimeCatalogItem"},
        "type": "array",
        "title": "Response List Overtime Technicians For Supervisor Api Overtime Supervisor Catalogs Technicians Get",
    }
    catalog_schema = schema["components"]["schemas"]["OvertimeCatalogItem"]
    assert set(catalog_schema["properties"]) == {"id", "name"}
    assert catalog_schema["properties"]["id"]["format"] == "uuid"
    patch = schema["paths"]["/api/overtime/requests/me/{request_id}"]["patch"]
    assert patch["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/OvertimeRequestUpdate"
    )


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
    assert not any(method in {"PUT", "DELETE"} for method, _ in methods_and_paths)
    assert ("POST", "/requests") in methods_and_paths
    assert ("PATCH", "/requests/me/{request_id}") in methods_and_paths
    assert ("POST", "/requests/me/{request_id}/cancel") in methods_and_paths
    assert ("POST", "/supervisor/requests/{request_id}/reject") in methods_and_paths


def test_technician_partial_update_preserves_omitted_and_forwards_explicit_null(monkeypatch):
    client = TestClient(create_app(monkeypatch, "technician"))
    response = client.patch(
        f"/api/overtime/requests/me/{REQUEST_ID}",
        json={"break_start_time": None, "break_end_time": None},
    )
    assert response.status_code == 200
    assert FakeOvertimeService.calls[-1] == (
        "update-own", {"break_start_time": None, "break_end_time": None}
    )
    assert client.patch(f"/api/overtime/requests/me/{REQUEST_ID}", json={}).status_code == 422
    assert client.patch(
        f"/api/overtime/requests/me/{REQUEST_ID}", json={"status": "cancelled"}
    ).status_code == 422


def test_technician_cancel_contract_has_no_required_payload(monkeypatch):
    client = TestClient(create_app(monkeypatch, "technician"))
    response = client.post(f"/api/overtime/requests/me/{REQUEST_ID}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
