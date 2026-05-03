import hashlib
import json
import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response


logger = logging.getLogger("app.observability")


REQUEST_ID_HEADER = "X-Request-ID"
APP_VERSION_HEADER = "x-app-version"
APP_PLATFORM_HEADER = "x-app-platform"


def _safe_header_value(value: str | None, max_length: int = 128) -> str | None:
    if not value:
        return None
    cleaned = "".join(ch for ch in value.strip() if ch.isprintable())
    return cleaned[:max_length] or None


def _request_id_from_headers(request: Request) -> str:
    incoming_request_id = _safe_header_value(request.headers.get(REQUEST_ID_HEADER), max_length=64)
    return incoming_request_id or str(uuid.uuid4())


def _normalised_path(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if path:
        return path
    root_path = request.scope.get("root_path", "")
    return f"{root_path}{request.url.path}"


def _first_attr(obj: Any, names: tuple[str, ...]) -> Any:
    for name in names:
        if isinstance(obj, dict) and name in obj:
            return obj.get(name)
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


def _role_value(role: Any) -> str | None:
    if role is None:
        return None
    value = getattr(role, "value", role)
    if value is None:
        return None
    return str(value)


def _current_user_from_state(request: Request) -> Any:
    state = request.state
    for attr_name in ("current_user", "user", "firebase_user", "usuario_actual"):
        if hasattr(state, attr_name):
            return getattr(state, attr_name)
    return None


def _anonymous_company_id(company_id: Any) -> str | None:
    if company_id is None:
        return None
    digest = hashlib.sha256(str(company_id).encode("utf-8")).hexdigest()
    return digest[:16]


def _user_context_from_state(request: Request) -> tuple[str | None, str | None]:
    current_user = _current_user_from_state(request)
    if current_user is None:
        return None, None

    role = _role_value(_first_attr(current_user, ("rol", "role", "user_role")))
    company_id = _first_attr(current_user, ("company_id", "company", "compania_id"))
    return role, _anonymous_company_id(company_id)


async def observability_middleware(
    request: Request,
    call_next: Callable[[Request], Any],
) -> Response:
    request_id = _request_id_from_headers(request)
    request.state.request_id = request_id

    started_at = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        logger.exception(
            "request_failed request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )
        raise
    finally:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        user_role, company_id_hash = _user_context_from_state(request)

        event = {
            "event": "http_request",
            "request_id": request_id,
            "method": request.method,
            "path": _normalised_path(request),
            "status_code": status_code,
            "duration_ms": duration_ms,
            "user_role": user_role,
            "company_id_hash": company_id_hash,
            "x_app_version": _safe_header_value(request.headers.get(APP_VERSION_HEADER)),
            "x_app_platform": _safe_header_value(request.headers.get(APP_PLATFORM_HEADER)),
        }
        logger.info(json.dumps(event, separators=(",", ":"), sort_keys=True))

        if "response" in locals():
            response.headers[REQUEST_ID_HEADER] = request_id
