from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest

from app.services.checklists import ChecklistService


NOW = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
TEMPLATE_ID = UUID("11111111-1111-1111-1111-111111111111")
MISSING_CATALOG_TEMPLATE_ID = UUID("22222222-2222-2222-2222-222222222222")
FIRST_STEP_ID = UUID("33333333-3333-3333-3333-333333333333")
SECOND_STEP_ID = UUID("44444444-4444-4444-4444-444444444444")


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class FakeSession:
    def __init__(self, rows):
        self.rows = rows
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return FakeResult(self.rows)


def template(*, template_id, order_id, unit_id, pasos):
    return SimpleNamespace(
        id=template_id,
        nombre="Plantilla de prueba",
        tipo_orden_id=order_id,
        tipo_unidad_id=unit_id,
        created_at=NOW,
        updated_at=NOW,
        pasos=pasos,
    )


def step(step_id, step_number, title):
    return SimpleNamespace(
        id=step_id,
        step_number=step_number,
        titulo=title,
        instrucciones=f"Instrucciones {title}",
        evidencia_schema={"foto": True},
    )


@pytest.mark.asyncio
async def test_list_admin_templates_uses_outer_joins_selectinload_and_stable_step_order():
    listed_template = template(
        template_id=TEMPLATE_ID,
        order_id=1,
        unit_id=2,
        pasos=[
            step(SECOND_STEP_ID, 2, "Segundo"),
            step(FIRST_STEP_ID, 1, "Primero"),
        ],
    )
    db = FakeSession([(listed_template, "Mantenimiento", "Ascensor")])

    templates = await ChecklistService(db).list_admin_templates()

    assert len(db.statements) == 1
    statement_sql = str(db.statements[0])
    assert "LEFT OUTER JOIN tipos_orden" in statement_sql
    assert "LEFT OUTER JOIN tipos_unidad" in statement_sql
    assert "NULLS LAST" in statement_sql
    assert "checklist_templates.nombre ASC" in statement_sql
    assert templates[0].tipo_orden_nombre == "Mantenimiento"
    assert templates[0].tipo_unidad_nombre == "Ascensor"
    assert templates[0].total_steps == 2
    assert [paso.step_number for paso in templates[0].pasos] == [1, 2]
    assert templates[0].created_at == NOW
    assert templates[0].updated_at == NOW


@pytest.mark.asyncio
async def test_list_admin_templates_keeps_ids_when_catalogs_are_missing_and_allows_empty_result():
    missing_catalog_template = template(
        template_id=MISSING_CATALOG_TEMPLATE_ID,
        order_id=999,
        unit_id=998,
        pasos=[],
    )
    db = FakeSession([(missing_catalog_template, None, None)])

    templates = await ChecklistService(db).list_admin_templates()

    assert templates[0].tipo_orden_id == 999
    assert templates[0].tipo_orden_nombre is None
    assert templates[0].tipo_unidad_id == 998
    assert templates[0].tipo_unidad_nombre is None
    assert templates[0].pasos == []

    empty_db = FakeSession([])
    assert await ChecklistService(empty_db).list_admin_templates() == []
