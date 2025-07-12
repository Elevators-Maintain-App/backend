import pytest
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.db.models.usuarios import Usuario, Rol
from app.db.models.compania import Compania
from app.db.models import TipoDocumento


# Event loop fixture removed - handled automatically by pytest-asyncio with asyncio_mode = auto


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
        id="12345678-1234-5678-9012-123456789abc",
        uid="test-firebase-uid",
        email="test@example.com",
        display_name="Test User",
        rol=Rol.SUPER_ADMIN,
        company_id="12345678-1234-5678-9012-123456789abc"
    )
    return usuario


@pytest.fixture
def mock_compania() -> Compania:
    """Create a mock company."""
    compania = Compania(
        id="12345678-1234-5678-9012-123456789abc",
        nombre="Test Company",
        email="company@test.com",
        tipo_documento_id=1,
        documento="123456789"
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
def sample_usuarios_list(mock_compania, mock_tipo_documento) -> list[Usuario]:
    """Create a list of sample users for testing."""
    usuarios = [
        Usuario(
            id="12345678-1234-5678-9012-123456789001",
            uid="firebase-uid1",
            email="user1@example.com",
            display_name="User One",
            rol=Rol.ADMIN,
            company_id="12345678-1234-5678-9012-123456789abc",
            document_id="12345",
            document_type_id=1,
            phone_number="+1234567890",
            is_active=True,
            created_at=datetime.now()
        ),
        Usuario(
            id="12345678-1234-5678-9012-123456789002",
            uid="firebase-uid2",
            email="user2@example.com",
            display_name="User Two",
            rol=Rol.TECHNICIAN,
            company_id="12345678-1234-5678-9012-123456789abc",
            document_id="12346",
            document_type_id=1,
            phone_number="+1234567891",
            is_active=True,
            created_at=datetime.now()
        ),
        Usuario(
            id="12345678-1234-5678-9012-123456789003",
            uid="firebase-uid3",
            email="user3@example.com",
            display_name="Another User",
            rol=Rol.TECHNICIAN,
            company_id="12345678-1234-5678-9012-123456789def",
            document_id="12347",
            document_type_id=1,
            phone_number="+1234567892",
            is_active=True,
            created_at=datetime.now()
        )
    ]
    
    # Set up relationships for each user
    for usuario in usuarios:
        usuario.company = mock_compania
        usuario.document_type = mock_tipo_documento
        
    return usuarios 