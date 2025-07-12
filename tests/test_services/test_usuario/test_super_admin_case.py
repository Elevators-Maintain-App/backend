import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from app.services.usuario.user_cases.super_admin import SuperAdminCase
from app.db.models.usuarios import Usuario, Rol
from app.db.models.compania import Compania
from app.db.models import TipoDocumento
from app.schemas.usuarios import UsuarioCreate
from app.auth.firebase import FirebaseUser, UsuarioFirebaseCreate


class TestSuperAdminCase:
    """Test suite for SuperAdminCase class."""

    @pytest.fixture
    def super_admin_case(self):
        """Create a SuperAdminCase instance for testing."""
        return SuperAdminCase()

    @pytest.fixture
    def usuario_create_data(self):
        """Create mock UsuarioCreate data."""
        return UsuarioCreate(
            email="newuser@example.com",
            display_name="New User",
            rol=Rol.ADMIN,
            company_id="test-company-id",
            document_type_id="doc-type-id",
            document="123456789"
        )

    @pytest.fixture
    def non_super_admin_user(self):
        """Create a user who is not a super admin."""
        return Usuario(
            id="regular-user-id",
            uid="regular-firebase-uid",
            email="regular@example.com",
            display_name="Regular User",
            rol=Rol.ADMIN,  # Not SUPER_ADMIN
            company_id="test-company-id"
        )

    def test_obtener_firebase_usuario_success(
        self, 
        super_admin_case, 
        mock_usuario_actual, 
        usuario_create_data, 
        mock_compania, 
        mock_tipo_documento
    ):
        """Test successful firebase user creation for super admin."""
        # Arrange
        params = {
            "usuario_actual": mock_usuario_actual,
            "usuario_nuevo": usuario_create_data,
            "compania": mock_compania,
            "tipo_documento": mock_tipo_documento
        }

        # Act
        result = super_admin_case.obtener_firebase_usuario(params)

        # Assert
        assert isinstance(result, UsuarioFirebaseCreate)
        assert result.email == usuario_create_data.email
        assert result.display_name == usuario_create_data.display_name

    def test_obtener_firebase_usuario_permission_denied(
        self, 
        super_admin_case, 
        non_super_admin_user, 
        usuario_create_data, 
        mock_compania, 
        mock_tipo_documento
    ):
        """Test firebase user creation with insufficient permissions."""
        # Arrange
        params = {
            "usuario_actual": non_super_admin_user,
            "usuario_nuevo": usuario_create_data,
            "compania": mock_compania,
            "tipo_documento": mock_tipo_documento
        }

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            super_admin_case.obtener_firebase_usuario(params)
        
        assert exc_info.value.status_code == 403
        assert "No tienes permisos para crear usuarios" in str(exc_info.value.detail)

    def test_obtener_usuario_a_guardar_success(
        self, 
        super_admin_case, 
        mock_usuario_actual, 
        usuario_create_data
    ):
        """Test successful user creation for super admin."""
        # Arrange
        firebase_uid = "new-firebase-uid"
        params = {
            "usuario_actual": mock_usuario_actual,
            "usuario_nuevo": usuario_create_data,
            "firebase_uid": firebase_uid
        }

        # Act
        result = super_admin_case.obtener_usuario_a_guardar(params)

        # Assert
        assert isinstance(result, UsuarioCreate)
        assert result.email == usuario_create_data.email
        assert result.display_name == usuario_create_data.display_name
        assert result.uid == firebase_uid

    def test_obtener_usuario_a_guardar_permission_denied(
        self, 
        super_admin_case, 
        non_super_admin_user, 
        usuario_create_data
    ):
        """Test user creation with insufficient permissions."""
        # Arrange
        firebase_uid = "new-firebase-uid"
        params = {
            "usuario_actual": non_super_admin_user,
            "usuario_nuevo": usuario_create_data,
            "firebase_uid": firebase_uid
        }

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            super_admin_case.obtener_usuario_a_guardar(params)
        
        assert exc_info.value.status_code == 403
        assert "No tienes permisos para crear usuarios" in str(exc_info.value.detail)

    def test_obtener_filtros_all_parameters(self, super_admin_case, mock_usuario_actual):
        """Test obtener_filtros with all parameters provided."""
        # Arrange
        search = "john"
        company_id = "company-123"
        rol = "ADMIN"

        # Act
        result = super_admin_case.obtener_filtros(
            mock_usuario_actual, 
            search, 
            company_id, 
            rol
        )

        # Assert
        expected = {
            "exact_filters": {
                "company_id": company_id,
                "rol": rol
            },
            "ilike_filters": {
                "display_name": f"%{search}%"
            },
            "like_filters": {}
        }
        assert result == expected

    def test_obtener_filtros_search_only(self, super_admin_case, mock_usuario_actual):
        """Test obtener_filtros with only search parameter."""
        # Arrange
        search = "jane"

        # Act
        result = super_admin_case.obtener_filtros(
            mock_usuario_actual, 
            search, 
            None, 
            None
        )

        # Assert
        expected = {
            "exact_filters": {},
            "ilike_filters": {
                "display_name": f"%{search}%"
            },
            "like_filters": {}
        }
        assert result == expected

    def test_obtener_filtros_company_and_rol_only(self, super_admin_case, mock_usuario_actual):
        """Test obtener_filtros with company_id and rol parameters."""
        # Arrange
        company_id = "company-456"
        rol = "TECHNICAL"

        # Act
        result = super_admin_case.obtener_filtros(
            mock_usuario_actual, 
            None, 
            company_id, 
            rol
        )

        # Assert
        expected = {
            "exact_filters": {
                "company_id": company_id,
                "rol": rol
            },
            "ilike_filters": {},
            "like_filters": {}
        }
        assert result == expected

    def test_obtener_filtros_no_parameters(self, super_admin_case, mock_usuario_actual):
        """Test obtener_filtros with no search parameters."""
        # Act
        result = super_admin_case.obtener_filtros(
            mock_usuario_actual, 
            None, 
            None, 
            None
        )

        # Assert
        expected = {
            "exact_filters": {},
            "ilike_filters": {},
            "like_filters": {}
        }
        assert result == expected

    def test_obtener_filtros_empty_strings(self, super_admin_case, mock_usuario_actual):
        """Test obtener_filtros with empty string parameters."""
        # Act
        result = super_admin_case.obtener_filtros(
            mock_usuario_actual, 
            "", 
            "", 
            ""
        )

        # Assert
        expected = {
            "exact_filters": {},
            "ilike_filters": {},
            "like_filters": {}
        }
        assert result == expected

    def test_obtener_filtros_whitespace_search(self, super_admin_case, mock_usuario_actual):
        """Test obtener_filtros with whitespace in search parameter."""
        # Arrange
        search = "  john doe  "

        # Act
        result = super_admin_case.obtener_filtros(
            mock_usuario_actual, 
            search, 
            None, 
            None
        )

        # Assert
        expected = {
            "exact_filters": {},
            "ilike_filters": {
                "display_name": f"%{search}%"
            },
            "like_filters": {}
        }
        assert result == expected

    @pytest.mark.parametrize("user_rol", [Rol.ADMIN, Rol.TECHNICIAN])
    def test_obtener_firebase_usuario_various_non_super_admin_roles(
        self, 
        super_admin_case, 
        usuario_create_data, 
        mock_compania, 
        mock_tipo_documento,
        user_rol
    ):
        """Test that various non-super-admin roles are denied permission."""
        # Arrange
        non_super_admin = Usuario(
            id="user-id",
            uid="user-uid",
            email="user@example.com",
            display_name="User",
            rol=user_rol,
            company_id="company-id"
        )
        
        params = {
            "usuario_actual": non_super_admin,
            "usuario_nuevo": usuario_create_data,
            "compania": mock_compania,
            "tipo_documento": mock_tipo_documento
        }

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            super_admin_case.obtener_firebase_usuario(params)
        
        assert exc_info.value.status_code == 403

    @pytest.mark.parametrize("user_rol", [Rol.ADMIN, Rol.TECHNICIAN])
    def test_obtener_usuario_a_guardar_various_non_super_admin_roles(
        self, 
        super_admin_case, 
        usuario_create_data,
        user_rol
    ):
        """Test that various non-super-admin roles are denied permission for user creation."""
        # Arrange
        non_super_admin = Usuario(
            id="user-id",
            uid="user-uid",
            email="user@example.com",
            display_name="User",
            rol=user_rol,
            company_id="company-id"
        )
        
        params = {
            "usuario_actual": non_super_admin,
            "usuario_nuevo": usuario_create_data,
            "firebase_uid": "firebase-uid"
        }

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            super_admin_case.obtener_usuario_a_guardar(params)
        
        assert exc_info.value.status_code == 403 