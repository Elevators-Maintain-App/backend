import os
from urllib.parse import urlparse


ALLOWED_TEST_DATABASE_HOSTS = {"db-test", "localhost", "127.0.0.1"}


class UnsafeTestDatabaseError(RuntimeError):
    """Raised when a pytest database configuration could touch non-test data."""


def _safe_database_description(database_url: str) -> str:
    parsed = urlparse(database_url)
    database = parsed.path.lstrip("/") or "<missing>"
    host = parsed.hostname or "<missing>"
    port = parsed.port or "<default>"
    username = parsed.username or "<missing>"
    return f"host={host} port={port} database={database} user={username}"


def validate_safe_test_database(environment: str | None, database_url: str | None) -> None:
    if environment != "test":
        raise UnsafeTestDatabaseError("ENVIRONMENT must be exactly 'test' before running pytest")

    if not database_url:
        raise UnsafeTestDatabaseError("DATABASE_URL is required before running pytest")

    parsed = urlparse(database_url)
    host = parsed.hostname
    database = parsed.path.lstrip("/")

    if not parsed.scheme or not host or not database:
        raise UnsafeTestDatabaseError("DATABASE_URL is invalid or incomplete")

    normalized_host = host.lower()
    if normalized_host not in ALLOWED_TEST_DATABASE_HOSTS:
        raise UnsafeTestDatabaseError(
            "Refusing to run pytest against a non-local database "
            f"({_safe_database_description(database_url)})"
        )

    if "test" not in database.lower():
        raise UnsafeTestDatabaseError(
            "Refusing to run pytest because the database name does not contain 'test' "
            f"({_safe_database_description(database_url)})"
        )


def validate_safe_test_database_from_env() -> None:
    validate_safe_test_database(
        environment=os.getenv("ENVIRONMENT"),
        database_url=os.getenv("DATABASE_URL"),
    )
