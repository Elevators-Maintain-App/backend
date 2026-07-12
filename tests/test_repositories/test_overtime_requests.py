from datetime import date, time
from uuid import UUID, uuid4

import pytest

from app.db.repositories.overtime_requests import OvertimeRequestRepository
from app.db.models.overtime_requests import OvertimeRequestStatus


COMPANY_ID = UUID("11111111-1111-1111-1111-111111111111")
SUPERVISOR_ID = UUID("44444444-4444-4444-4444-444444444444")
REQUEST_ID = UUID("66666666-6666-6666-6666-666666666666")


class EmptyResult:
    def scalars(self):
        return self

    def unique(self):
        return self

    def one_or_none(self):
        return None

    def scalar_one_or_none(self):
        return None


class RecordingDB:
    def __init__(self):
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return EmptyResult()


class CountResult:
    def scalar_one(self):
        return 7


class PageRowsResult(EmptyResult):
    def all(self):
        return []


class RecordingPageDB:
    def __init__(self):
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return CountResult() if len(self.statements) % 2 else PageRowsResult()


@pytest.mark.asyncio
async def test_supervisor_review_query_is_company_scoped_assigned_and_for_update():
    db = RecordingDB()
    repository = OvertimeRequestRepository(db)
    await repository.lock_for_supervisor_review(
        request_id=REQUEST_ID,
        company_id=COMPANY_ID,
        supervisor_id=SUPERVISOR_ID,
    )
    sql = str(db.statement)
    params = db.statement.compile().params.values()
    assert "overtime_requests.company_id" in sql
    assert "overtime_requests.authorizing_supervisor_id" in sql
    assert "FOR UPDATE" in sql
    assert REQUEST_ID in params
    assert COMPANY_ID in params
    assert SUPERVISOR_ID in params


@pytest.mark.asyncio
async def test_technician_mutation_query_is_owned_company_scoped_and_for_update():
    db = RecordingDB()
    repository = OvertimeRequestRepository(db)
    technician_id = UUID("33333333-3333-3333-3333-333333333333")

    await repository.lock_for_technician_mutation(
        request_id=REQUEST_ID,
        company_id=COMPANY_ID,
        technician_id=technician_id,
    )

    sql = str(db.statement)
    params = db.statement.compile().params.values()
    assert "overtime_requests.company_id" in sql
    assert "overtime_requests.technician_id" in sql
    assert "FOR UPDATE" in sql
    assert REQUEST_ID in params
    assert COMPANY_ID in params
    assert technician_id in params


@pytest.mark.asyncio
async def test_overlap_query_is_scoped_uses_half_open_intersection_and_can_exclude_request():
    db = RecordingDB()
    repository = OvertimeRequestRepository(db)

    assert not await repository.has_active_overlap(
        company_id=COMPANY_ID,
        technician_id=UUID("33333333-3333-3333-3333-333333333333"),
        work_date=date(2026, 7, 8),
        entry_time=time(10),
        exit_time=time(12),
        exclude_request_id=REQUEST_ID,
    )

    sql = str(db.statement)
    params = db.statement.compile().params.values()
    assert "overtime_requests.company_id" in sql
    assert "overtime_requests.technician_id" in sql
    assert "overtime_requests.work_date" in sql
    assert "overtime_requests.entry_time <" in sql
    assert "overtime_requests.exit_time >" in sql
    assert "overtime_requests.id !=" in sql
    assert REQUEST_ID in params
    assert {"pending", "approved", "adjusted"} <= {
        value.value if hasattr(value, "value") else value
        for parameter in db.statement.compile().params.values()
        for value in (parameter if isinstance(parameter, (list, tuple)) else [parameter])
    }


@pytest.mark.asyncio
async def test_technician_page_uses_database_count_same_filters_offset_and_stable_order():
    db = RecordingPageDB()
    repository = OvertimeRequestRepository(db)
    rows, total = await repository.page_for_technician(
        company_id=COMPANY_ID,
        technician_id=UUID("33333333-3333-3333-3333-333333333333"),
        status=None,
        date_from=date(2026, 6, 12),
        date_to=date(2026, 7, 12),
        offset=40,
        limit=20,
    )
    count_sql, items_sql = map(str, db.statements)
    for fragment in (
        "overtime_requests.company_id",
        "overtime_requests.technician_id",
        "overtime_requests.work_date >=",
        "overtime_requests.work_date <=",
    ):
        assert fragment in count_sql and fragment in items_sql
    assert "count(" in count_sql.lower()
    assert "ORDER BY overtime_requests.work_date DESC, overtime_requests.submitted_at DESC, overtime_requests.id DESC" in items_sql
    assert db.statements[1].compile().params["param_1"] == 20
    assert db.statements[1].compile().params["param_2"] == 40
    assert rows == [] and total == 7


@pytest.mark.asyncio
async def test_supervisor_page_keeps_assignment_company_and_technician_filter_in_count_and_items():
    db = RecordingPageDB()
    repository = OvertimeRequestRepository(db)
    technician_id = UUID("33333333-3333-3333-3333-333333333333")
    await repository.page_for_supervisor(
        company_id=COMPANY_ID,
        supervisor_id=SUPERVISOR_ID,
        technician_id=technician_id,
        status=OvertimeRequestStatus.CANCELLED,
        date_from=date(2026, 6, 12),
        date_to=date(2026, 7, 12),
        offset=0,
        limit=20,
    )
    count_sql, items_sql = map(str, db.statements)
    for fragment in (
        "overtime_requests.company_id",
        "overtime_requests.authorizing_supervisor_id",
        "overtime_requests.technician_id",
        "overtime_requests.status",
    ):
        assert fragment in count_sql and fragment in items_sql
    assert "CASE WHEN" in items_sql
    assert "overtime_requests.id DESC" in items_sql


@pytest.mark.asyncio
async def test_supervisor_export_count_and_rows_share_visibility_filters_without_pagination():
    db = RecordingPageDB()
    repository = OvertimeRequestRepository(db)
    filters = {
        "company_id": COMPANY_ID,
        "supervisor_id": SUPERVISOR_ID,
        "technician_id": UUID("33333333-3333-3333-3333-333333333333"),
        "status": OvertimeRequestStatus.CANCELLED,
        "date_from": date(2026, 6, 12),
        "date_to": date(2026, 7, 12),
    }
    assert await repository.count_for_supervisor_export(**filters) == 7
    rows = await repository.list_for_supervisor_export(**filters)
    count_sql, items_sql = map(str, db.statements)
    for fragment in (
        "overtime_requests.company_id",
        "overtime_requests.authorizing_supervisor_id",
        "overtime_requests.technician_id",
        "overtime_requests.status",
        "overtime_requests.work_date >=",
        "overtime_requests.work_date <=",
    ):
        assert fragment in count_sql and fragment in items_sql
    assert " LIMIT " not in items_sql and " OFFSET " not in items_sql
    assert "usuarios.display_name ASC" in items_sql
    assert "overtime_requests.work_date ASC" in items_sql
    assert "overtime_requests.entry_time ASC" in items_sql
    assert "overtime_requests.id ASC" in items_sql
    assert rows == []
