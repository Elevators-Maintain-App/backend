import pytest

from app.core.database_safety import UnsafeTestDatabaseError, validate_safe_test_database
from scripts.bootstrap_test_database import bootstrap_test_database


def test_accepts_isolated_test_database():
    validate_safe_test_database(
        "test",
        "postgresql+asyncpg://vertione_test_user:secret@db-test:5432/vertione_test",
    )


@pytest.mark.parametrize("environment", [None, "", "production"])
def test_rejects_non_test_environment(environment):
    with pytest.raises(UnsafeTestDatabaseError, match="ENVIRONMENT"):
        validate_safe_test_database(
            environment,
            "postgresql+asyncpg://vertione_test_user:secret@db-test:5432/vertione_test",
        )


def test_rejects_missing_database_url():
    with pytest.raises(UnsafeTestDatabaseError, match="DATABASE_URL"):
        validate_safe_test_database("test", None)


@pytest.mark.parametrize(
    "database_url",
    [
        "postgresql+asyncpg://user:secret@db.example.com:5432/vertione_test",
        "postgresql+asyncpg://user:secret@ec2-1-2-3-4.compute-1.amazonaws.com:5432/vertione_test",
        "postgresql+asyncpg://user:secret@project.us-central1.cloudsql.google.com:5432/vertione_test",
    ],
)
def test_rejects_remote_database_hosts(database_url):
    with pytest.raises(UnsafeTestDatabaseError, match="non-local database"):
        validate_safe_test_database("test", database_url)


def test_rejects_database_name_without_test():
    with pytest.raises(UnsafeTestDatabaseError, match="database name"):
        validate_safe_test_database(
            "test",
            "postgresql+asyncpg://vertione_test_user:secret@db-test:5432/vertione",
        )


@pytest.mark.parametrize("database_url", ["not-a-url", "postgresql+asyncpg:///vertione_test"])
def test_rejects_invalid_database_url(database_url):
    with pytest.raises(UnsafeTestDatabaseError, match="invalid"):
        validate_safe_test_database("test", database_url)


@pytest.mark.asyncio
async def test_bootstrap_validates_loads_models_and_creates_schema_in_order():
    calls = []

    def validate(environment, database_url):
        calls.append(("validate", environment, database_url))

    def load_models():
        calls.append(("load_models",))

    async def create_tables():
        calls.append(("create_tables",))

    await bootstrap_test_database(
        validate=validate,
        load_models=load_models,
        create_tables=create_tables,
    )

    assert calls == [
        (
            "validate",
            "test",
            "postgresql+asyncpg://vertione_test_user:vertione_test_password@db-test:5432/vertione_test",
        ),
        ("load_models",),
        ("create_tables",),
    ]


@pytest.mark.asyncio
async def test_bootstrap_stops_before_loading_models_when_validation_fails():
    calls = []

    def validate(environment, database_url):
        calls.append(("validate", environment, database_url))
        raise RuntimeError("unsafe")

    def load_models():
        calls.append(("load_models",))

    async def create_tables():
        calls.append(("create_tables",))

    with pytest.raises(RuntimeError, match="unsafe"):
        await bootstrap_test_database(
            validate=validate,
            load_models=load_models,
            create_tables=create_tables,
        )

    assert calls == [
        (
            "validate",
            "test",
            "postgresql+asyncpg://vertione_test_user:vertione_test_password@db-test:5432/vertione_test",
        )
    ]
