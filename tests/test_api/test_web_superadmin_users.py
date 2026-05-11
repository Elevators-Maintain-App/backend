from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module
from types import SimpleNamespace
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.testclient import TestClient

from app.auth.firebase import get_current_firebase_user
from app.db.session import get_db
from app.middleware.observability import observability_middleware


web_superadmin = import_module("app.api.routes.web_superadmin")


COMPANY_ID = UUID("33333333-3333-3333-3333-333333333333")
OTHER_COMPANY_ID = UUID("44444444-4444-4444-4444-444444444444")
NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class DummyDB:
    pass


def user_payload(uid: str = "firebase-user-1") -> dict:
    return {
        "id": "55555555-5555-5555-5555-555555555555",
        "uid": uid,
        "display_name": "Usuario Contrato",
        "email": "user@example.com",
        "phone": "+50700000000",
        "phone_number": "+50700000000",
        "role": "admin",
        "company_id": str(COMPANY_ID),
        "company_name": "Compania contrato",
        "photo_url": None,
        "is_active": True,
        "status": "active",
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
        "document_id": "DOC-1",
        "document_type_id": 1,
        "document_type_name": "Cedula",
        "client_id": None,
        "nivel": None,
    }


class FakeWebSuperAdminService:
    calls = []
    existing_uids = {"firebase-user-1"}
    duplicate_email = "duplicado@example.com"

    def __init__(self, db):
        self.db = db

    async def get_users_summary(self):
        self.calls.append(("summary",))
        return {"total_users": 123}

    async def get_users(
        self,
        *,
        page,
        page_size,
        search=None,
        role=None,
        company_id=None,
        status_value=None,
    ):
        self.calls.append(
            (
                "list",
                {
                    "page": page,
                    "page_size": page_size,
                    "search": search,
                    "role": role,
                    "company_id": company_id,
                    "status_value": status_value,
                },
            )
        )
        item = user_payload()
        item["role"] = role or "admin"
        return {
            "items": [item],
            "data": [item],
            "total": 123,
            "page": page,
            "page_size": page_size,
            "total_pages": 7,
        }

    async def get_user_detail(self, uid):
        self.calls.append(("detail", {"uid": uid}))
        if uid not in self.existing_uids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return user_payload(uid)

    async def create_user(self, *, current_user, payload, request_id=None):
        self.calls.append(
            (
                "create",
                {
                    "current_user": current_user.uid,
                    "email": str(payload.email),
                    "role": payload.role or payload.rol,
                    "company_id": payload.company_id,
                    "request_id": request_id,
                },
            )
        )
        if str(payload.email) == self.duplicate_email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El email ya existe")
        created = user_payload("created-user-uid")
        created["email"] = str(payload.email)
        created["display_name"] = payload.display_name
        created["role"] = payload.role or payload.rol
        created["company_id"] = str(payload.company_id) if payload.company_id else None
        return created

    async def update_user(self, uid, payload):
        self.calls.append(
            (
                "update",
                {
                    "uid": uid,
                    "display_name": payload.display_name,
                    "status": payload.status,
                },
            )
        )
        if uid not in self.existing_uids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        updated = user_payload(uid)
        if payload.display_name:
            updated["display_name"] = payload.display_name
        if payload.status:
            updated["status"] = payload.status
            updated["is_active"] = payload.status == "active"
        return updated

    async def disable_user(self, *, uid, current_user):
        self.calls.append(("disable", {"uid": uid, "current_user": current_user.uid}))
        if uid == current_user.uid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes inhabilitar tu propio usuario",
            )
        if uid not in self.existing_uids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return {"uid": uid, "status": "inactive", "message": "Usuario inhabilitado"}

    async def delete_user(self, *, uid, current_user):
        self.calls.append(("delete", {"uid": uid, "current_user": current_user.uid}))
        if uid == current_user.uid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes eliminar tu propio usuario",
            )
        if uid not in self.existing_uids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return {"uid": uid, "deleted": True, "message": "Usuario eliminado"}

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
        return [{"id": "66666666-6666-6666-6666-666666666666", "name": "Cliente contrato"}]


def auth_user(role: str, uid: str = "web-superadmin-auth-user"):
    return SimpleNamespace(
        uid=uid,
        rol=SimpleNamespace(value=role),
        role=role,
        company_id=COMPANY_ID,
        created_time=NOW,
    )


def create_app(role: str | None = "superAdmin", uid: str = "web-superadmin-auth-user") -> FastAPI:
    FakeWebSuperAdminService.calls = []
    app = FastAPI()
    app.middleware("http")(observability_middleware)
    app.include_router(web_superadmin.router, prefix="/api/web/superadmin")

    async def fake_db():
        return DummyDB()

    async def fake_auth_dependency(request: Request):
        user = auth_user(role or "anonymous", uid=uid)
        request.state.current_user = user
        return user

    app.dependency_overrides[get_db] = fake_db
    if role is not None:
        app.dependency_overrides[get_current_firebase_user] = fake_auth_dependency

    return app


def client(monkeypatch, role: str | None = "superAdmin", uid: str = "web-superadmin-auth-user"):
    monkeypatch.setattr(web_superadmin, "WebSuperAdminService", FakeWebSuperAdminService)
    return TestClient(create_app(role=role, uid=uid))


def test_superadmin_can_list_users(monkeypatch):
    response = client(monkeypatch).get("/api/web/superadmin/users")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["uid"] == "firebase-user-1"
    assert payload["data"][0]["uid"] == "firebase-user-1"
    assert FakeWebSuperAdminService.calls[0][0] == "list"


def test_non_superadmin_user_receives_403(monkeypatch):
    response = client(monkeypatch, role="admin").get("/api/web/superadmin/users")

    assert response.status_code == 403
    assert FakeWebSuperAdminService.calls == []


def test_list_supports_pagination(monkeypatch):
    response = client(monkeypatch).get(
        "/api/web/superadmin/users",
        params={
            "page": 2,
            "page_size": 20,
            "search": "contrato",
            "role": "technician",
            "company_id": str(OTHER_COMPANY_ID),
            "status": "active",
        },
    )

    assert response.status_code == 200
    assert response.json()["page"] == 2
    assert FakeWebSuperAdminService.calls == [
        (
            "list",
            {
                "page": 2,
                "page_size": 20,
                "search": "contrato",
                "role": "technician",
                "company_id": OTHER_COMPANY_ID,
                "status_value": "active",
            },
        )
    ]


def test_existing_user_detail_returns_200(monkeypatch):
    response = client(monkeypatch).get("/api/web/superadmin/users/firebase-user-1")

    assert response.status_code == 200
    assert response.json()["uid"] == "firebase-user-1"


def test_missing_user_detail_returns_404(monkeypatch):
    response = client(monkeypatch).get("/api/web/superadmin/users/missing-user")

    assert response.status_code == 404


def test_create_user_success(monkeypatch):
    response = client(monkeypatch).post(
        "/api/web/superadmin/users",
        json={
            "display_name": "Usuario Nuevo",
            "email": "nuevo@example.com",
            "phone": "+50700000001",
            "role": "admin",
            "company_id": str(COMPANY_ID),
            "password": "Secret123",
        },
        headers={"X-Request-ID": "web-create-user"},
    )

    assert response.status_code == 201
    assert response.json()["uid"] == "created-user-uid"
    assert FakeWebSuperAdminService.calls[0][0] == "create"
    assert FakeWebSuperAdminService.calls[0][1]["request_id"] == "web-create-user"


def test_create_user_with_invalid_email_returns_422(monkeypatch):
    response = client(monkeypatch).post(
        "/api/web/superadmin/users",
        json={
            "display_name": "Usuario Nuevo",
            "email": "email-invalido",
            "role": "admin",
            "company_id": str(COMPANY_ID),
        },
    )

    assert response.status_code == 422
    assert FakeWebSuperAdminService.calls == []


def test_create_user_with_duplicate_email_returns_409(monkeypatch):
    response = client(monkeypatch).post(
        "/api/web/superadmin/users",
        json={
            "display_name": "Usuario Duplicado",
            "email": FakeWebSuperAdminService.duplicate_email,
            "role": "admin",
            "company_id": str(COMPANY_ID),
        },
    )

    assert response.status_code == 409


def test_update_user_success(monkeypatch):
    response = client(monkeypatch).patch(
        "/api/web/superadmin/users/firebase-user-1",
        json={"display_name": "Usuario Actualizado", "status": "inactive"},
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Usuario Actualizado"
    assert response.json()["status"] == "inactive"


def test_update_missing_user_returns_404(monkeypatch):
    response = client(monkeypatch).patch(
        "/api/web/superadmin/users/missing-user",
        json={"display_name": "Usuario Actualizado"},
    )

    assert response.status_code == 404


def test_disable_user_success(monkeypatch):
    response = client(monkeypatch).post("/api/web/superadmin/users/firebase-user-1/disable")

    assert response.status_code == 200
    assert response.json() == {
        "uid": "firebase-user-1",
        "status": "inactive",
        "message": "Usuario inhabilitado",
    }


def test_disable_missing_user_returns_404(monkeypatch):
    response = client(monkeypatch).post("/api/web/superadmin/users/missing-user/disable")

    assert response.status_code == 404


def test_delete_user_success(monkeypatch):
    response = client(monkeypatch).delete("/api/web/superadmin/users/firebase-user-1")

    assert response.status_code == 200
    assert response.json() == {
        "uid": "firebase-user-1",
        "deleted": True,
        "message": "Usuario eliminado",
    }


def test_delete_missing_user_returns_404(monkeypatch):
    response = client(monkeypatch).delete("/api/web/superadmin/users/missing-user")

    assert response.status_code == 404


def test_required_endpoints_do_not_return_404_or_405(monkeypatch):
    test_client = client(monkeypatch)
    requests = [
        test_client.get("/api/web/superadmin/users"),
        test_client.get("/api/web/superadmin/users/firebase-user-1"),
        test_client.post(
            "/api/web/superadmin/users",
            json={
                "display_name": "Usuario Nuevo",
                "email": "nuevo@example.com",
                "role": "admin",
                "company_id": str(COMPANY_ID),
            },
        ),
        test_client.patch(
            "/api/web/superadmin/users/firebase-user-1",
            json={"display_name": "Usuario Actualizado"},
        ),
        test_client.post("/api/web/superadmin/users/firebase-user-1/disable"),
        test_client.delete("/api/web/superadmin/users/firebase-user-1"),
    ]

    assert all(response.status_code not in {404, 405} for response in requests)


def test_self_delete_is_not_allowed(monkeypatch):
    response = client(monkeypatch, uid="firebase-user-1").delete(
        "/api/web/superadmin/users/firebase-user-1"
    )

    assert response.status_code == 400
    assert "propio usuario" in response.json()["detail"]


def test_self_disable_is_not_allowed(monkeypatch):
    response = client(monkeypatch, uid="firebase-user-1").post(
        "/api/web/superadmin/users/firebase-user-1/disable"
    )

    assert response.status_code == 400
    assert "propio usuario" in response.json()["detail"]


def test_super_admin_alias_can_list_users(monkeypatch):
    response = client(monkeypatch, role="super_admin").get("/api/web/superadmin/users")

    assert response.status_code == 200
