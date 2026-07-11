from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo


PANAMA_TIMEZONE = ZoneInfo("America/Panama")
REGULAR_WORKDAY_MINUTES = 480


class OvertimeValidationError(ValueError):
    """Raised when an overtime work date or same-day schedule is invalid."""


@dataclass(frozen=True)
class OvertimeCalculation:
    worked_minutes: int
    regular_minutes: int
    overtime_minutes: int


def _minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def _validate_minute_precision(*values: time | None) -> None:
    if any(value is not None and (value.second != 0 or value.microsecond != 0) for value in values):
        raise OvertimeValidationError(
            "Entry, exit, and break times must have exact minute precision; "
            "seconds and microseconds are not allowed"
        )


def _panama_date(now: date | datetime) -> date:
    if isinstance(now, datetime):
        if now.tzinfo is None:
            now = now.replace(tzinfo=PANAMA_TIMEZONE)
        else:
            now = now.astimezone(PANAMA_TIMEZONE)
        return now.date()
    return now


def validate_current_calendar_week(work_date: date, *, now: date | datetime) -> None:
    """Validate that work_date is in now's Monday-Sunday week in Panama."""
    current_date = _panama_date(now)
    monday = current_date.fromordinal(current_date.toordinal() - current_date.weekday())
    sunday = monday.fromordinal(monday.toordinal() + 6)
    if not monday <= work_date <= sunday:
        raise OvertimeValidationError(
            "Work date must belong to the current Monday-Sunday calendar week in America/Panama"
        )


def calculate_overtime(
    *,
    work_date: date,
    entry_time: time,
    exit_time: time,
    now: date | datetime,
    break_start_time: time | None = None,
    break_end_time: time | None = None,
) -> OvertimeCalculation:
    """Validate and calculate a same-day work period using integer minutes."""
    _validate_minute_precision(entry_time, exit_time, break_start_time, break_end_time)
    validate_current_calendar_week(work_date, now=now)

    entry_minutes = _minutes(entry_time)
    exit_minutes = _minutes(exit_time)
    if exit_minutes <= entry_minutes:
        raise OvertimeValidationError(
            "Exit time must be after entry time; overnight shifts are not allowed"
        )

    if (break_start_time is None) != (break_end_time is None):
        raise OvertimeValidationError("Break start and end times must be provided together")

    break_minutes = 0
    if break_start_time is not None and break_end_time is not None:
        break_start_minutes = _minutes(break_start_time)
        break_end_minutes = _minutes(break_end_time)
        if break_start_minutes >= break_end_minutes:
            raise OvertimeValidationError("Break start time must be before break end time")
        if break_start_minutes < entry_minutes:
            raise OvertimeValidationError("Break cannot start before entry time")
        if break_end_minutes > exit_minutes:
            raise OvertimeValidationError("Break cannot end after exit time")
        break_minutes = break_end_minutes - break_start_minutes

    worked_minutes = exit_minutes - entry_minutes - break_minutes
    if worked_minutes <= 0:
        raise OvertimeValidationError("Worked duration must be greater than zero minutes")

    regular_minutes = min(worked_minutes, REGULAR_WORKDAY_MINUTES)
    overtime_minutes = max(worked_minutes - REGULAR_WORKDAY_MINUTES, 0)
    return OvertimeCalculation(
        worked_minutes=worked_minutes,
        regular_minutes=regular_minutes,
        overtime_minutes=overtime_minutes,
    )
