#!/usr/bin/env python3
import asyncio
import sys
from collections.abc import Callable

from app.core.config import settings
from app.core.database_safety import validate_safe_test_database
from app.db.session import Base, engine


def _safe_database_description() -> str:
    url = engine.url
    return f"host={url.host} port={url.port or '<default>'} database={url.database} user={url.username}"


def import_models() -> None:
    import app.db.models  # noqa: F401


async def create_schema() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def bootstrap_test_database(
    *,
    validate: Callable[[str | None, str | None], None] = validate_safe_test_database,
    load_models: Callable[[], None] = import_models,
    create_tables: Callable[[], object] = create_schema,
) -> None:
    validate(settings.environment, str(settings.database_url))
    load_models()
    await create_tables()


async def _run() -> int:
    try:
        await bootstrap_test_database()
        print(f"Test database schema created safely ({_safe_database_description()})")
        return 0
    except Exception as exc:
        print(f"Failed to bootstrap test database safely: {exc}", file=sys.stderr)
        return 1
    finally:
        await engine.dispose()


def main() -> int:
    return asyncio.run(_run())


if __name__ == "__main__":
    sys.exit(main())
