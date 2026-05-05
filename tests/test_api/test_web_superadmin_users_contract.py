from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module
from types import SimpleNamespace
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.auth.firebase import get_current_firebase_user
from app.db.session import get_db
from app.middleware.observability import observability_middleware


web_superadmin = import_module("app.api.routes.web_superadmin")


COMPANY_ID = UUID("33333333-3333-3333-3333-333333333333")
NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class DummyDB:
    pass


class FakeWebSuperAdminService:
    calls = []

    def __init__(self, db):
        self.db = db

    async def get_users_summary(self):
        self.calls.append(("summary",))
        return {"total_users": 123}

    async def get_users(self, *, page, page_size, search=None, role=None):
        self.calls.append(
            (
                "list",
                {
                    "page": page,
                    "page_size": page_size,
                    "search": search,
                    "role": role,
                },
            )
        )
        return {
            "data": [
                {
                    "uid": "firebase-user-1",
                    "email": "user@example.invalid",
                    "display_name": "Usuario Contrato",
                    "role": role or "admin",
                    "company_id": COMPANY_ID,
                    "company_name": "Compania contrato",
                    "photo_url": None,
                    "is_active": True,
                }
            ],
            "total": 123,
            "page": page,
            "page_size": page_size,
            "total_pages": 13,
        }

    async def get_companies_catalog(self):
        self.calls.append(("companies",))
        return [{"id": str(COMPANY_ID), "name": "Compania contrato"}]

    async def get_document_types_catalog(self):
        self.calls.append(("document_types",))
        return [{"id": "1", "name": "Cedula"}]

    async def get_technical_levels_catalog(self, *, company_id=None):
        self.calls.append(("technical_levels", {"company_id": company_id}))
        return [{"id": "nivel-1", "name": "Nivel 1"}]

    async def get_company_clients_catalog(self, *, company_id):
        self.calls.append(("clients", {"company_id": company_id}))
        return [{"id": "55555555-5555-5555-5555-555555555555", "name": "Cliente contrato"}]


class FakeUsuarioService:
    calls = []

    def __init__(self, db):
        self.db = db

    async def create(self, usuario_actual, usuario_data, photo=None, request_id=None):
        self.calls.append(
            {
                "usuario_actual": usuario_actual.uid,
                "usuario_data": usuario_data,
                "has_photo": photo is not None,
                "request_id": request_id,
            }
        )
        return {
            "id": UUID("44444444-4444-4444-4444-444444444444"),
            "uid": "created-user-uid",
            "company_id": usuario_data["company_id"],
            "display_name": usuario_data["display_name"],
            "document_id": usuario_data["document_id"],
            "document_type_id": usuario_data["document_type_id"],
            "email": usuario_data["email"],
            "phone_number": usuario_data["phone_number"],
            "rol": usuario_data["rol"].value,
            "client_id": usuario_data["client_id"],
            "nivel": usuario_data["nivel"],
            "zona_geografica_id": usuario_data["zona_geografica_id"],
            "photo_url": None,
            "is_active": usuario_data["is_active"],
            "created_at": NOW,
            "updated_at": NOW,
            "company_name": "Compania contrato",
            "document_type_name": "Cedula",
        }


def auth_user(role: str):
    return SimpleNamespace(
        uid="web-superadmin-auth-user",
        rol=SimpleNamespace(value=role),
        role=role,
        company_id=COMPANY_ID,
        created_time=NOW,
    )


def create_app(role: str | None = "superAdmin") -> FastAPI:
    FakeWebSuperAdminService.calls = []
    FakeUsuarioService.calls = []
    app = FastAPI()
    app.middleware("http")(observability_middleware)
    app.include_router(web_superadmin.router, prefix="/api/web/superadmin")

    async def fake_db():
        return DummyDB()

    async def fake_auth_dependency(request: Request):
        user = auth_user(role or "anonymous")
        request.state.current_user = user
        return user

    app.dependency_overrides[get_db] = fake_db
    if role is not None:
        app.dependency_overrides[get_current_firebase_user] = fake_auth_dependency

    return app


def test_web_superadmin_summary_without_token_is_not_allowed_and_keeps_request_id(
    monkeypatch,
):
    monkeypatch.setattr(web_superadmin, "WebSuperAdminService", FakeWebSuperAdminService)
    client = TestClient(create_app(role=None))

    response = client.get(
        "/api/web/superadmin/users/summary",
        headers={"X-Request-ID": "web-superadmin-summary-no-token"},
    )

    assert response.status_code in {401, 403}
    assert response.headers["X-Request-ID"] == "web-superadmin-summary-no-token"
    assert FakeWebSuperAdminService.calls == []


def test_web_superadmin_summary_with_invalid_role_is_forbidden(monkeypatch):
    monkeypatch.setattr(web_superadmin, "WebSuperAdminService", FakeWebSuperAdminService)
    client = TestClient(create_app(role="admin"))

    response = client.get(
        "/api/web/superadmin/users/summary",
        headers={"X-Request-ID": "web-superadmin-summary-invalid-role"},
    )

    assert response.status_code == 403
    assert response.headers["X-Request-ID"] == "web-superadmin-summary-invalid-role"
    assert FakeWebSuperAdminService.calls == []


def test_web_superadmin_summary_with_superadmin_returns_total_users(monkeypatch):
    monkeypatch.setattr(web_superadmin, "WebSuperAdminService", FakeWebSuperAdminService)
    client = TestClient(create_app(role="superAdmin"))

    response = client.get(
        "/api/web/superadmin/users/summary",
        headers={"X-Request-ID": "web-superadmin-summary-allowed"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "web-superadmin-summary-allowed"
    assert response.json() == {"total_users": 123}
    assert FakeWebSuperAdminService.calls == [("summary",)]


def test_web_superadmin_users_with_superadmin_returns_paginated_contract(monkeypatch):
    monkeypatch.setattr(web_superadmin, "WebSuperAdminService", FakeWebSuperAdminService)
    client = TestClient(create_app(role="superAdmin"))

    response = client.get(
        "/api/web/superadmin/users",
        headers={"X-Request-ID": "web-superadmin-users-allowed"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "web-superadmin-users-allowed"
    payload = response.json()
    assert set(payload.keys()) == {"data", "total", "page", "page_size", "total_pages"}
    assert payload["total"] == 123
    assert payload["page"] == 1
    assert payload["page_size"] == 10
    assert payload["total_pages"] == 13
    assert payload["data"][0] == {
        "uid": "firebase-user-1",
        "email": "user@example.invalid",
        "display_name": "Usuario Contrato",
        "role": "admin",
        "company_id": str(COMPANY_ID),
        "company_name": "Compania contrato",
        "photo_url": None,
        "is_active": True,
    }


def test_web_superadmin_users_search_and_role_do_not_break(monkeypatch):
    monkeypatch.setattr(web_superadmin, "WebSuperAdminService", FakeWebSuperAdminService)
    client = TestClient(create_app(role="superAdmin"))

    response = client.get(
        "/api/web/superadmin/users",
        params={
            "page": 2,
            "page_size": 20,
            "search": "contrato",
            "role": "technician",
        },
        headers={"X-Request-ID": "web-superadmin-users-filtered"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "web-superadmin-users-filtered"
    assert FakeWebSuperAdminService.calls == [
        (
            "list",
            {
                "page": 2,
                "page_size": 20,
                "search": "contrato",
                "role": "technician",
            },
        )
    ]
    assert response.json()["data"][0]["role"] == "technician"


def test_web_superadmin_catalogs_are_protected_and_return_minimal_items(monkeypatch):
    monkeypatch.setattr(web_superadmin, "WebSuperAdminService", FakeWebSuperAdminService)
    client = TestClient(create_app(role="superAdmin"))

    response = client.get(
        "/api/web/superadmin/catalogs/companies",
        headers={"X-Request-ID": "web-superadmin-companies"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "web-superadmin-companies"
    assert response.json() == [{"id": str(COMPANY_ID), "name": "Compania contrato"}]
    assert FakeWebSuperAdminService.calls == [("companies",)]


def test_web_superadmin_company_clients_catalog_filters_by_company(monkeypatch):
    monkeypatch.setattr(web_superadmin, "WebSuperAdminService", FakeWebSuperAdminService)
    client = TestClient(create_app(role="superAdmin"))

    response = client.get(
        f"/api/web/superadmin/companies/{COMPANY_ID}/clients",
        headers={"X-Request-ID": "web-superadmin-company-clients"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "web-superadmin-company-clients"
    assert response.json() == [
        {"id": "55555555-5555-5555-5555-555555555555", "name": "Cliente contrato"}
    ]
    assert FakeWebSuperAdminService.calls == [
        ("clients", {"company_id": COMPANY_ID})
    ]


def test_web_superadmin_create_user_uses_form_contract(monkeypatch):
    monkeypatch.setattr(web_superadmin, "UsuarioService", FakeUsuarioService)
    client = TestClient(create_app(role="superAdmin"))

    client_id = "55555555-5555-5555-5555-555555555555"
    response = client.post(
        "/api/web/superadmin/users",
        data={
            "company_id": str(COMPANY_ID),
            "display_name": "Cliente Nuevo",
            "document_id": "DOC-CLIENT",
            "document_type_id": "1",
            "email": "cliente.nuevo@example.invalid",
            "phone_number": "+50700000001",
            "rol": "client",
            "client_id": client_id,
            "is_active": "true",
        },
        headers={"X-Request-ID": "web-superadmin-create-user"},
    )

    assert response.status_code == 201
    assert response.headers["X-Request-ID"] == "web-superadmin-create-user"
    assert FakeUsuarioService.calls[0]["usuario_data"]["client_id"] == UUID(client_id)
    assert FakeUsuarioService.calls[0]["usuario_data"]["rol"].value == "client"
    assert response.json()["client_id"] == client_id
