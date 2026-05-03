import json

from fastapi import FastAPI, Response, status
from fastapi.testclient import TestClient

from app.middleware.observability import observability_middleware


def create_test_app() -> FastAPI:
    app = FastAPI()
    app.middleware("http")(observability_middleware)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/created", status_code=status.HTTP_201_CREATED)
    async def created(response: Response):
        response.headers["X-Original-Header"] = "kept"
        return {"created": True}

    return app


def test_observability_middleware_keeps_simple_route_working():
    client = TestClient(create_test_app())

    response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}


def test_observability_middleware_adds_request_id_header():
    client = TestClient(create_test_app())

    response = client.get("/health", headers={"X-Request-ID": "mobile-request-1"})

    assert response.headers["X-Request-ID"] == "mobile-request-1"


def test_observability_middleware_preserves_original_status_code():
    client = TestClient(create_test_app())

    response = client.get("/created")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.headers["X-Original-Header"] == "kept"


def test_observability_middleware_logs_safe_structured_event(caplog):
    client = TestClient(create_test_app())

    with caplog.at_level("INFO", logger="app.observability"):
        client.get(
            "/health",
            headers={
                "X-App-Version": "1.2.3",
                "X-App-Platform": "ios",
            },
        )

    event = json.loads(caplog.records[-1].message)
    assert event["event"] == "http_request"
    assert event["method"] == "GET"
    assert event["path"] == "/health"
    assert event["status_code"] == status.HTTP_200_OK
    assert event["x_app_version"] == "1.2.3"
    assert event["x_app_platform"] == "ios"
    assert "duration_ms" in event
