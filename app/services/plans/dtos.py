from dataclasses import dataclass


@dataclass(frozen=True)
class LimitCheckResult:
    allowed: bool
    resource: str
    current_usage: int | float
    plan_limit: int | float | None
    code: str | None = None
    message: str | None = None
