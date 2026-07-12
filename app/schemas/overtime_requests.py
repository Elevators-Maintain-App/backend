from datetime import date, datetime, time
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.db.models.overtime_requests import OvertimeRequestEventType, OvertimeRequestStatus


def _validate_minute_time(value: time | None) -> time | None:
    if value is not None and (value.second or value.microsecond):
        raise ValueError("Los horarios deben tener precisión exacta de minutos")
    return value


def _non_blank(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("El texto no puede estar vacío")
    return normalized


class OvertimeCatalogItem(BaseModel):
    id: UUID
    name: str


class OvertimeScheduleBase(BaseModel):
    entry_time: time
    break_start_time: time | None = None
    break_end_time: time | None = None
    exit_time: time
    activity: str = Field(min_length=3, max_length=2000)
    project_id: UUID

    model_config = ConfigDict(extra="forbid")

    @field_validator("entry_time", "break_start_time", "break_end_time", "exit_time")
    @classmethod
    def validate_minute_precision(cls, value: time | None) -> time | None:
        return _validate_minute_time(value)

    @field_validator("activity")
    @classmethod
    def validate_activity(cls, value: str) -> str:
        return _non_blank(value)

    @model_validator(mode="after")
    def validate_break_pair(self):
        if (self.break_start_time is None) != (self.break_end_time is None):
            raise ValueError("El inicio y fin del receso deben enviarse juntos")
        return self


class OvertimeRequestCreate(OvertimeScheduleBase):
    work_date: date
    authorizing_supervisor_id: UUID


class OvertimeRequestUpdate(BaseModel):
    work_date: date | None = None
    entry_time: time | None = None
    break_start_time: time | None = None
    break_end_time: time | None = None
    exit_time: time | None = None
    activity: str | None = Field(default=None, min_length=3, max_length=2000)
    project_id: UUID | None = None
    authorizing_supervisor_id: UUID | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("entry_time", "break_start_time", "break_end_time", "exit_time")
    @classmethod
    def validate_minute_precision(cls, value: time | None) -> time | None:
        return _validate_minute_time(value)

    @field_validator("activity")
    @classmethod
    def validate_activity(cls, value: str | None) -> str | None:
        return _non_blank(value) if value is not None else None

    @model_validator(mode="after")
    def validate_patch(self):
        if not self.model_fields_set:
            raise ValueError("Debe enviar al menos un campo modificable")
        nullable_fields = {"break_start_time", "break_end_time"}
        for field_name in self.model_fields_set - nullable_fields:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} no puede ser null")
        return self


class OvertimeApproveRequest(BaseModel):
    note: str | None = Field(default=None, max_length=2000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("note")
    @classmethod
    def normalize_optional_note(cls, value: str | None) -> str | None:
        return _non_blank(value) if value is not None else None


class OvertimeAdjustAndApproveRequest(OvertimeScheduleBase):
    note: str = Field(min_length=1, max_length=2000)

    @field_validator("note")
    @classmethod
    def validate_note(cls, value: str) -> str:
        return _non_blank(value)


class OvertimeRejectRequest(BaseModel):
    note: str = Field(min_length=1, max_length=2000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("note")
    @classmethod
    def validate_note(cls, value: str) -> str:
        return _non_blank(value)


class OvertimeRequestSummary(BaseModel):
    id: UUID
    work_date: date
    activity: str
    project: OvertimeCatalogItem
    technician: OvertimeCatalogItem
    authorizing_supervisor: OvertimeCatalogItem
    worked_minutes: int
    regular_minutes: int
    overtime_minutes: int
    status: OvertimeRequestStatus
    submitted_at: datetime
    reviewed_at: datetime | None


class OvertimeRequestEventOut(BaseModel):
    id: UUID
    actor_user_id: UUID
    event_type: OvertimeRequestEventType
    previous_status: OvertimeRequestStatus | None
    new_status: OvertimeRequestStatus
    note: str | None
    snapshot_before: dict[str, Any] | None
    snapshot_after: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OvertimeRequestDetail(OvertimeRequestSummary):
    entry_time: time
    break_start_time: time | None
    break_end_time: time | None
    exit_time: time
    supervisor_note: str | None
    created_at: datetime
    updated_at: datetime
    events: list[OvertimeRequestEventOut]


class OvertimeRequestPage(BaseModel):
    items: list[OvertimeRequestSummary]
    page: int
    page_size: int
    total: int
    total_pages: int
    date_from: date
    date_to: date
