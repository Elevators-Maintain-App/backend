import pytest
import asyncio
from typing import Generator
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_safety import validate_safe_test_database_from_env

validate_safe_test_database_from_env()

from app.db.models.usuarios import Usuario, Rol
from app.db.models.compania import Compania
from app.db.models import TipoDocumento

from uuid import uuid4


def pytest_sessionstart(session):
    validate_safe_test_database_from_env()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def mock_usuario_actual() -> Usuario:
    """Create a mock current user."""
    usuario = Usuario(
        id=uuid4(),
        uid="test-firebase-uid",
        email="test@example.com",
        display_name="Test User",
        rol=Rol.SUPER_ADMIN,
        company_id=uuid4(),
    )
    return usuario


@pytest.fixture
def mock_compania() -> Compania:
    """Create a mock company."""
    compania = Compania(
        id=uuid4(),
        nombre="Test Company",
        email="company@test.com",
    )
    return compania


@pytest.fixture
def mock_tipo_documento() -> TipoDocumento:
    """Create a mock document type."""
    tipo_documento = TipoDocumento(
        id=1,
        nombre="Cédula"
    )
    return tipo_documento


@pytest.fixture
def sample_usuarios_list() -> list[Usuario]:
    """Create a list of sample users for testing."""
    return [
        Usuario(
            id="user1",
            uid="firebase-uid1",
            email="user1@example.com",
            display_name="User One",
            rol=Rol.ADMIN,
            company_id="company1"
        ),
        Usuario(
            id="user2",
            uid="firebase-uid2",
            email="user2@example.com",
            display_name="User Two",
            rol=Rol.TECHNICIAN,
            company_id="company1"
        ),
        Usuario(
            id="user3",
            uid="firebase-uid3",
            email="user3@example.com",
            display_name="Another User",
            rol=Rol.TECHNICIAN,
            company_id="company2"
        )
    ]
