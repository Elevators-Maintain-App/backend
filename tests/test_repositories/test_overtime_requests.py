from uuid import UUID

import pytest

from app.db.repositories.overtime_requests import OvertimeRequestRepository


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


class RecordingDB:
    def __init__(self):
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return EmptyResult()


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
