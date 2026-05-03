from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.auth.firebase import get_current_firebase_user
from app.db.session import get_db
from app.middleware.observability import observability_middleware


estados_orden = import_module("app.api.routes.estados_orden")
prioridades = import_module("app.api.routes.prioridades")
tipos_documento = import_module("app.api.routes.tipos_documento")
tipos_evidencia = import_module("app.api.routes.tipos_evidencia")
tipos_orden = import_module("app.api.routes.tipos_orden")
tipos_unidad = import_module("app.api.routes.tipos_unidad")


COMPANY_ID = UUID("33333333-3333-3333-3333-333333333333")
NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


CATALOG_ENDPOINTS = [
    (estados_orden, "estado_orden_crud", "/api/estados-orden/", {"nombre": "Estado contrato"}),
    (prioridades, "prioridad_crud", "/api/prioridades/", {"nombre": "Prioridad contrato"}),
    (
        tipos_documento,
        "tipo_documento_crud",
        "/api/tipos-documento/",
        {"nombre": "Documento contrato", "descripcion": "Contrato", "is_system_wide": False},
    ),
    (
        tipos_evidencia,
        "tipo_evidencia_crud",
        "/api/tipos-evidencia/",
        {"nombre": "Evidencia contrato"},
    ),
    (tipos_orden, "tipo_orden_crud", "/api/tipos-orden/", {"nombre": "Orden contrato"}),
    (tipos_unidad, "tipo_unidad_crud", "/api/tipos-unidad/", {"nombre": "Unidad contrato"}),
]


class DummyDB:
    pass


class FakeCrud:
    def __init__(self):
        self.get_by_field_calls = []
        self.create_calls = []

    async def get_by_field(self, db, *, field, value):
        self.get_by_field_calls.append((field, value))
        return None

    async def create(self, db, *, obj_in):
        data = obj_in.model_dump()
        self.create_calls.append(data)
        return {
            "id": 99,
            "nombre": data["nombre"],
            "descripcion": data.get("descripcion"),
            "is_system_wide": data.get("is_system_wide", False),
            "compania_id": data.get("owner_compania_id"),
            "created_at": NOW,
            "updated_at": NOW,
        }


def auth_user(role: str):
    return SimpleNamespace(
        uid="catalog-auth-user",
        rol=SimpleNamespace(value=role),
        role=role,
        company_id=COMPANY_ID,
        created_time=NOW,
    )


def create_app(role: str | None = "admin") -> FastAPI:
    app = FastAPI()
    app.middleware("http")(observability_middleware)
    app.include_router(estados_orden.router, prefix="/api/estados-orden")
    app.include_router(prioridades.router, prefix="/api/prioridades")
    app.include_router(tipos_documento.router, prefix="/api/tipos-documento")
    app.include_router(tipos_evidencia.router, prefix="/api/tipos-evidencia")
    app.include_router(tipos_orden.router, prefix="/api/tipos-orden")
    app.include_router(tipos_unidad.router, prefix="/api/tipos-unidad")

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


@pytest.mark.parametrize(("module", "crud_name", "path", "payload"), CATALOG_ENDPOINTS)
def test_catalog_post_without_token_is_not_allowed_and_keeps_request_id(
    monkeypatch,
    module,
    crud_name,
    path,
    payload,
):
    fake_crud = FakeCrud()
    monkeypatch.setattr(module, crud_name, fake_crud)
    client = TestClient(create_app(role=None))

    response = client.post(
        path,
        json=payload,
        headers={"X-Request-ID": "catalog-post-no-token"},
    )

    assert response.status_code not in {404, 405}
    assert response.status_code in {401, 403}
    assert response.headers["X-Request-ID"] == "catalog-post-no-token"
    assert fake_crud.create_calls == []


@pytest.mark.parametrize(("module", "crud_name", "path", "payload"), CATALOG_ENDPOINTS)
def test_catalog_post_with_invalid_role_is_forbidden(
    monkeypatch,
    module,
    crud_name,
    path,
    payload,
):
    fake_crud = FakeCrud()
    monkeypatch.setattr(module, crud_name, fake_crud)
    client = TestClient(create_app(role="technician"))

    response = client.post(
        path,
        json=payload,
        headers={"X-Request-ID": "catalog-post-invalid-role"},
    )

    assert response.status_code == 403
    assert response.headers["X-Request-ID"] == "catalog-post-invalid-role"
    assert fake_crud.create_calls == []


@pytest.mark.parametrize("allowed_role", ["superAdmin", "admin"])
@pytest.mark.parametrize(("module", "crud_name", "path", "payload"), CATALOG_ENDPOINTS)
def test_catalog_post_with_allowed_role_reaches_handler_and_preserves_contract(
    monkeypatch,
    allowed_role,
    module,
    crud_name,
    path,
    payload,
):
    fake_crud = FakeCrud()
    monkeypatch.setattr(module, crud_name, fake_crud)
    client = TestClient(create_app(role=allowed_role))

    response = client.post(
        path,
        json=payload,
        headers={"X-Request-ID": "catalog-post-allowed-role"},
    )

    assert response.status_code == 201
    assert response.headers["X-Request-ID"] == "catalog-post-allowed-role"
    assert fake_crud.get_by_field_calls == [("nombre", payload["nombre"])]
    assert fake_crud.create_calls[0]["nombre"] == payload["nombre"]

    body = response.json()
    assert body["id"] == 99
    assert body["nombre"] == payload["nombre"]
    assert "created_at" in body
    assert "updated_at" in body
