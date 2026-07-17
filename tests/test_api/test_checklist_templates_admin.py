from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from app.api.routes import checklists
from app.auth.firebase import get_current_firebase_user
from app.db.session import get_db


NOW = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
TEMPLATE_ID = UUID("11111111-1111-1111-1111-111111111111")
STEP_ID = UUID("22222222-2222-2222-2222-222222222222")


class FakeChecklistService:
    create_conflict = False
    create_calls = []

    def __init__(self, db):
        self.db = db

    async def list_admin_templates(self):
        return [
            {
                "id": TEMPLATE_ID,
                "nombre": "Mantenimiento - Ascensor",
                "tipo_orden_id": 1,
                "tipo_orden_nombre": "Mantenimiento",
                "tipo_unidad_id": 2,
                "tipo_unidad_nombre": "Ascensor",
                "total_steps": 1,
                "created_at": NOW,
                "updated_at": NOW,
                "pasos": [
                    {
                        "id": STEP_ID,
                        "step_number": 1,
                        "titulo": "Preparación",
                        "instrucciones": "Preparar la visita.",
                        "evidencia_schema": {"foto": True},
                    }
                ],
            },
            {
                "id": UUID("33333333-3333-3333-3333-333333333333"),
                "nombre": "Catálogo faltante",
                "tipo_orden_id": 999,
                "tipo_orden_nombre": None,
                "tipo_unidad_id": 998,
                "tipo_unidad_nombre": None,
                "total_steps": 0,
                "created_at": None,
                "updated_at": None,
                "pasos": [],
            },
        ]

    async def create_template_with_items(self, payload):
        self.create_calls.append(payload.model_dump())
        if self.create_conflict:
            raise HTTPException(409, "Ya existe una plantilla para esa combinación")
        return {
            "id": TEMPLATE_ID,
            "nombre": payload.nombre,
            "tipo_orden_id": payload.tipo_orden_id,
            "tipo_unidad_id": payload.tipo_unidad_id,
            "pasos_ids": [STEP_ID],
        }


def create_app(monkeypatch, role: str) -> FastAPI:
    FakeChecklistService.create_conflict = False
    FakeChecklistService.create_calls = []
    monkeypatch.setattr(checklists, "ChecklistService", FakeChecklistService)
    app = FastAPI()
    app.include_router(checklists.router, prefix="/api/checklists")

    async def fake_db():
        yield SimpleNamespace()

    async def fake_auth(request: Request):
        user = SimpleNamespace(uid="checklist-admin", rol=role)
        request.state.current_user = user
        return user

    app.dependency_overrides[get_db] = fake_db
    app.dependency_overrides[get_current_firebase_user] = fake_auth
    return app


def test_admin_lists_templates_with_exact_shape_and_openapi_exposes_get_and_post(monkeypatch):
    app = create_app(monkeypatch, "admin")
    response = TestClient(app).get("/api/checklists/templates")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(TEMPLATE_ID),
            "nombre": "Mantenimiento - Ascensor",
            "tipo_orden_id": 1,
            "tipo_orden_nombre": "Mantenimiento",
            "tipo_unidad_id": 2,
            "tipo_unidad_nombre": "Ascensor",
            "total_steps": 1,
            "created_at": "2026-07-16T12:00:00Z",
            "updated_at": "2026-07-16T12:00:00Z",
            "pasos": [
                {
                    "id": str(STEP_ID),
                    "step_number": 1,
                    "titulo": "Preparación",
                    "instrucciones": "Preparar la visita.",
                    "evidencia_schema": {"foto": True},
                }
            ],
        },
        {
            "id": "33333333-3333-3333-3333-333333333333",
            "nombre": "Catálogo faltante",
            "tipo_orden_id": 999,
            "tipo_orden_nombre": None,
            "tipo_unidad_id": 998,
            "tipo_unidad_nombre": None,
            "total_steps": 0,
            "created_at": None,
            "updated_at": None,
            "pasos": [],
        },
    ]
    operations = app.openapi()["paths"]["/api/checklists/templates"]
    assert {"get", "post"}.issubset(operations)


def test_non_admin_cannot_list_templates(monkeypatch):
    response = TestClient(create_app(monkeypatch, "technician")).get(
        "/api/checklists/templates"
    )

    assert response.status_code == 403


def test_post_and_existing_conflict_contract_remain_available(monkeypatch):
    app = create_app(monkeypatch, "admin")
    client = TestClient(app)
    payload = {
        "nombre": "Nueva plantilla",
        "tipo_orden_id": 3,
        "tipo_unidad_id": 4,
        "pasos": [
            {
                "step_number": 1,
                "titulo": "Paso",
                "instrucciones": "Instrucciones",
                "evidencia_schema": {},
            }
        ],
    }

    assert client.post("/api/checklists/templates", json=payload).status_code == 201
    FakeChecklistService.create_conflict = True
    conflict = client.post("/api/checklists/templates", json=payload)
    assert conflict.status_code == 409
    assert conflict.json() == {"detail": "Ya existe una plantilla para esa combinación"}
