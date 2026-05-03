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


usuarios = import_module("app.api.routes.usuarios")


COMPANY_ID = UUID("33333333-3333-3333-3333-333333333333")
USER_ID = UUID("44444444-4444-4444-4444-444444444444")
USER_UID = "firebase-user-to-update"
CREATED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
UPDATED_AT = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)


class DummyDB:
    pass


class FakeUsuarioService:
    calls = []

    def __init__(self, db):
        self.db = db

    async def update(self, uid, usuario_in):
        self.calls.append((uid, usuario_in.model_dump(exclude_unset=True)))
        return {
            "id": USER_ID,
            "uid": uid,
            "company_id": COMPANY_ID,
            "display_name": usuario_in.display_name,
            "document_id": "DOC-1",
            "document_type_id": 1,
            "email": "updated@example.invalid",
            "phone_number": "+50700000000",
            "rol": "admin",
            "client_id": None,
            "nivel": None,
            "zona_geografica_id": None,
            "photo_url": None,
            "is_active": True,
            "created_at": CREATED_AT,
            "updated_at": UPDATED_AT,
            "company_name": "Compania contrato",
            "document_type_name": "Cedula",
        }


def auth_user(role: str):
    return SimpleNamespace(
        uid="request-user",
        rol=SimpleNamespace(value=role),
        role=role,
        company_id=COMPANY_ID,
        created_time=CREATED_AT,
    )


def create_app(role: str | None = "admin") -> FastAPI:
    FakeUsuarioService.calls = []
    app = FastAPI()
    app.middleware("http")(observability_middleware)
    app.include_router(usuarios.router, prefix="/api/usuarios")

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


def test_update_usuario_without_token_is_not_allowed_and_keeps_request_id(monkeypatch):
    monkeypatch.setattr(usuarios, "UsuarioService", FakeUsuarioService)
    client = TestClient(create_app(role=None))

    response = client.put(
        f"/api/usuarios/{USER_UID}",
        json={"display_name": "Nombre actualizado"},
        headers={"X-Request-ID": "usuarios-update-no-token"},
    )

    assert response.status_code in {401, 403}
    assert response.headers["X-Request-ID"] == "usuarios-update-no-token"
    assert FakeUsuarioService.calls == []


def test_update_usuario_with_invalid_role_is_forbidden(monkeypatch):
    monkeypatch.setattr(usuarios, "UsuarioService", FakeUsuarioService)
    client = TestClient(create_app(role="technician"))

    response = client.put(
        f"/api/usuarios/{USER_UID}",
        json={"display_name": "Nombre actualizado"},
        headers={"X-Request-ID": "usuarios-update-invalid-role"},
    )

    assert response.status_code == 403
    assert response.headers["X-Request-ID"] == "usuarios-update-invalid-role"
    assert FakeUsuarioService.calls == []


def test_update_usuario_with_valid_role_reaches_handler_and_preserves_contract(monkeypatch):
    monkeypatch.setattr(usuarios, "UsuarioService", FakeUsuarioService)
    client = TestClient(create_app(role="admin"))

    response = client.put(
        f"/api/usuarios/{USER_UID}",
        json={"display_name": "Nombre actualizado"},
        headers={"X-Request-ID": "usuarios-update-valid-role"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "usuarios-update-valid-role"
    assert FakeUsuarioService.calls == [
        (USER_UID, {"display_name": "Nombre actualizado"})
    ]

    payload = response.json()
    assert set(payload.keys()) == {
        "company_id",
        "display_name",
        "document_id",
        "document_type_id",
        "email",
        "phone_number",
        "rol",
        "client_id",
        "nivel",
        "zona_geografica_id",
        "photo_url",
        "is_active",
        "id",
        "uid",
        "created_at",
        "updated_at",
        "company_name",
        "document_type_name",
    }
    assert payload["uid"] == USER_UID
    assert payload["display_name"] == "Nombre actualizado"
    assert payload["rol"] == "admin"
