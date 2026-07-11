from datetime import date, datetime, time, timezone

import pytest

from app.services.overtime import (
    OvertimeValidationError,
    calculate_overtime,
    validate_current_calendar_week,
)


MONDAY = date(2026, 7, 6)
NOW = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)


def calculate(entry: time, exit_: time, break_start=None, break_end=None, **kwargs):
    return calculate_overtime(
        work_date=kwargs.get("work_date", MONDAY),
        entry_time=entry,
        break_start_time=break_start,
        break_end_time=break_end,
        exit_time=exit_,
        now=kwargs.get("now", NOW),
    )


@pytest.mark.parametrize(
    "entry,break_start,break_end,exit_,expected",
    [
        (time(7), time(12), time(12, 30), time(15, 30), (480, 480, 0)),
        (time(7), time(12), time(12, 30), time(16, 30), (540, 480, 60)),
        (time(6, 30), time(12), time(12, 30), time(15, 30), (510, 480, 30)),
        (time(7), None, None, time(15, 30), (510, 480, 30)),
        (time(6, 45), time(12, 10), time(12, 40), time(16, 5), (530, 480, 50)),
    ],
)
def test_required_calculation_examples(entry, break_start, break_end, exit_, expected):
    result = calculate(entry, exit_, break_start, break_end)
    assert (result.worked_minutes, result.regular_minutes, result.overtime_minutes) == expected
    assert all(isinstance(value, int) for value in expected)


@pytest.mark.parametrize("exit_", [time(6, 59), time(7)])
def test_rejects_exit_before_or_equal_to_entry(exit_):
    with pytest.raises(OvertimeValidationError, match="overnight shifts are not allowed"):
        calculate(time(7), exit_)


def test_rejects_overnight_schedule():
    with pytest.raises(OvertimeValidationError, match="overnight"):
        calculate(time(23), time(1))


@pytest.mark.parametrize(
    "break_start,break_end",
    [(time(12), None), (None, time(12, 30))],
)
def test_rejects_incomplete_break_pair(break_start, break_end):
    with pytest.raises(OvertimeValidationError, match="provided together"):
        calculate(time(7), time(16), break_start, break_end)


@pytest.mark.parametrize(
    "break_start,break_end,message",
    [
        (time(12, 30), time(12), "before break end"),
        (time(12), time(12), "before break end"),
        (time(6, 59), time(7, 30), "before entry"),
        (time(15, 30), time(16, 1), "after exit"),
    ],
)
def test_rejects_invalid_break_bounds(break_start, break_end, message):
    with pytest.raises(OvertimeValidationError, match=message):
        calculate(time(7), time(16), break_start, break_end)


def test_rejects_nonpositive_worked_duration_after_break():
    with pytest.raises(OvertimeValidationError, match="greater than zero"):
        calculate(time(7), time(8), time(7), time(8))


@pytest.mark.parametrize("work_date", [date(2026, 7, 6), date(2026, 7, 12)])
def test_accepts_monday_and_sunday_of_current_week(work_date):
    validate_current_calendar_week(work_date, now=NOW)


def test_rejects_day_before_current_monday():
    with pytest.raises(OvertimeValidationError, match="current Monday-Sunday"):
        validate_current_calendar_week(date(2026, 7, 5), now=NOW)


def test_week_changes_at_panama_monday():
    sunday = datetime(2026, 7, 12, 23, 59)
    monday = datetime(2026, 7, 13, 0, 0)
    validate_current_calendar_week(date(2026, 7, 6), now=sunday)
    with pytest.raises(OvertimeValidationError):
        validate_current_calendar_week(date(2026, 7, 12), now=monday)


def test_aware_utc_datetime_is_converted_to_panama_near_day_change():
    utc_monday = datetime(2026, 7, 13, 3, 30, tzinfo=timezone.utc)
    validate_current_calendar_week(date(2026, 7, 12), now=utc_monday)
    with pytest.raises(OvertimeValidationError):
        validate_current_calendar_week(date(2026, 7, 13), now=utc_monday)


def test_panama_week_changes_at_0500_utc():
    utc_panama_monday = datetime(2026, 7, 13, 5, 0, tzinfo=timezone.utc)
    validate_current_calendar_week(date(2026, 7, 13), now=utc_panama_monday)
    with pytest.raises(OvertimeValidationError):
        validate_current_calendar_week(date(2026, 7, 12), now=utc_panama_monday)


def test_calculation_can_skip_week_validation_for_supervisor_review():
    utc_panama_monday = datetime(2026, 7, 13, 5, 0, tzinfo=timezone.utc)
    result = calculate_overtime(
        work_date=date(2026, 7, 12),
        entry_time=time(7),
        break_start_time=time(12),
        break_end_time=time(12, 30),
        exit_time=time(18, 30),
        now=utc_panama_monday,
        validate_week=False,
    )
    assert (result.worked_minutes, result.regular_minutes, result.overtime_minutes) == (660, 480, 180)


def test_regular_minutes_are_capped_and_overtime_is_never_negative():
    short_day = calculate(time(7), time(8))
    long_day = calculate(time(6), time(20))
    assert short_day.regular_minutes == 60
    assert short_day.overtime_minutes == 0
    assert long_day.regular_minutes == 480
    assert long_day.overtime_minutes == 360


def test_valid_days_with_and_without_break():
    assert calculate(time(7), time(8)).worked_minutes == 60
    assert calculate(time(7), time(8), time(7, 15), time(7, 30)).worked_minutes == 45


@pytest.mark.parametrize(
    "entry,exit_,break_start,break_end",
    [
        (time(7, 0, 1), time(16), None, None),
        (time(7), time(16, 0, 1), None, None),
        (time(7), time(16), time(12, 0, 1), time(12, 30)),
        (time(7), time(16), time(12), time(12, 30, 1)),
    ],
)
def test_rejects_seconds_in_any_schedule_time(entry, exit_, break_start, break_end):
    with pytest.raises(OvertimeValidationError, match="seconds and microseconds are not allowed"):
        calculate(entry, exit_, break_start, break_end)


@pytest.mark.parametrize(
    "entry,exit_,break_start,break_end",
    [
        (time(7, microsecond=1), time(16), None, None),
        (time(7), time(16, microsecond=1), None, None),
        (time(7), time(16), time(12, microsecond=1), time(12, 30)),
        (time(7), time(16), time(12), time(12, 30, microsecond=1)),
    ],
)
def test_rejects_microseconds_in_any_schedule_time(entry, exit_, break_start, break_end):
    with pytest.raises(OvertimeValidationError, match="seconds and microseconds are not allowed"):
        calculate(entry, exit_, break_start, break_end)
