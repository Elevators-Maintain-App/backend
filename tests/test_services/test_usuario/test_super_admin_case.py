import pytest
from fastapi import HTTPException
from uuid import uuid4

from app.services.usuario.user_cases.super_admin import SuperAdminCase
from app.db.models.usuarios import Usuario, Rol
from app.schemas.usuarios import UsuarioCreate
from app.auth.firebase import UsuarioFirebaseCreate
from app.services.usuario.interfaces.usuario_case import (
    CrearUsuarioParams,
    CrearUsuarioFirebaseParams,
)


class TestSuperAdminCase:
    """Test suite for SuperAdminCase class."""

    @pytest.fixture
    def super_admin_case(self):
        """Create a SuperAdminCase instance for testing."""
        return SuperAdminCase()

    @pytest.fixture
    def usuario_create_data(self):
        """Create valid UsuarioCreate data."""
        return UsuarioCreate(
            email="newuser@example.com",
            display_name="New User",
            rol=Rol.ADMIN,
            company_id=uuid4(),
            document_type_id=1,
            document_id="123456789",
            phone_number="6000-0000",
        )

    @pytest.fixture
    def non_super_admin_user(self):
        """Create a user who is not a super admin."""
        return Usuario(
            id=uuid4(),
            uid="regular-firebase-uid",
            email="regular@example.com",
            display_name="Regular User",
            rol=Rol.ADMIN,
            company_id=uuid4(),
        )

    def test_obtener_firebase_usuario_success(
        self,
        super_admin_case,
        mock_usuario_actual,
        usuario_create_data,
        mock_compania,
        mock_tipo_documento,
    ):
        """Test successful firebase user creation for super admin."""
        params = CrearUsuarioFirebaseParams(
            usuario_actual=mock_usuario_actual,
            usuario_nuevo=usuario_create_data,
            compania=mock_compania,
            tipo_documento=mock_tipo_documento,
            cliente=None,
        )

        result = super_admin_case.obtener_firebase_usuario(params)

        assert isinstance(result, UsuarioFirebaseCreate)
        assert result.email == usuario_create_data.email
        assert result.display_name == usuario_create_data.display_name
        assert result.company_id == mock_compania.id
        assert result.rol == usuario_create_data.rol

    def test_obtener_firebase_usuario_permission_denied(
        self,
        super_admin_case,
        non_super_admin_user,
        usuario_create_data,
        mock_compania,
        mock_tipo_documento,
    ):
        """Test firebase user creation with insufficient permissions."""
        params = CrearUsuarioFirebaseParams(
            usuario_actual=non_super_admin_user,
            usuario_nuevo=usuario_create_data,
            compania=mock_compania,
            tipo_documento=mock_tipo_documento,
            cliente=None,
        )

        with pytest.raises(HTTPException) as exc_info:
            super_admin_case.obtener_firebase_usuario(params)

        assert exc_info.value.status_code == 403
        assert "No tienes permisos para crear usuarios" in str(exc_info.value.detail)

    def test_obtener_usuario_a_guardar_success(
        self,
        super_admin_case,
        mock_usuario_actual,
        usuario_create_data,
    ):
        """Test successful user object creation for super admin."""
        firebase_uid = "new-firebase-uid"
        params = CrearUsuarioParams(
            usuario_actual=mock_usuario_actual,
            usuario_nuevo=usuario_create_data,
            firebase_uid=firebase_uid,
        )

        result = super_admin_case.obtener_usuario_a_guardar(params)

        assert result.email == usuario_create_data.email
        assert result.display_name == usuario_create_data.display_name
        assert result.uid == firebase_uid
        assert result.rol == usuario_create_data.rol
        assert result.company_id == usuario_create_data.company_id

    def test_obtener_usuario_a_guardar_permission_denied(
        self,
        super_admin_case,
        non_super_admin_user,
        usuario_create_data,
    ):
        """Test user creation with insufficient permissions."""
        params = CrearUsuarioParams(
            usuario_actual=non_super_admin_user,
            usuario_nuevo=usuario_create_data,
            firebase_uid="new-firebase-uid",
        )

        with pytest.raises(HTTPException) as exc_info:
            super_admin_case.obtener_usuario_a_guardar(params)

        assert exc_info.value.status_code == 403
        assert "No tienes permisos para crear usuarios" in str(exc_info.value.detail)

    def test_obtener_filtros_all_parameters(self, super_admin_case, mock_usuario_actual):
        """Test obtener_filtros_para_listar_usuarios with all parameters provided."""
        search = "john"
        company_id = "company-123"
        rol = "ADMIN"

        result = super_admin_case.obtener_filtros_para_listar_usuarios(
            mock_usuario_actual,
            search,
            company_id,
            rol,
        )

        expected = {
            "exact_filters": {
                "company_id": company_id,
                "rol": rol,
            },
            "ilike_filters": {
                "display_name": f"%{search}%",
            },
            "like_filters": {},
        }
        assert result == expected

    def test_obtener_filtros_search_only(self, super_admin_case, mock_usuario_actual):
        """Test obtener_filtros_para_listar_usuarios with only search parameter."""
        search = "jane"

        result = super_admin_case.obtener_filtros_para_listar_usuarios(
            mock_usuario_actual,
            search,
            None,
            None,
        )

        expected = {
            "exact_filters": {},
            "ilike_filters": {
                "display_name": f"%{search}%",
            },
            "like_filters": {},
        }
        assert result == expected

    def test_obtener_filtros_company_and_rol_only(self, super_admin_case, mock_usuario_actual):
        """Test obtener_filtros_para_listar_usuarios with company_id and rol."""
        company_id = "company-456"
        rol = "TECHNICIAN"

        result = super_admin_case.obtener_filtros_para_listar_usuarios(
            mock_usuario_actual,
            None,
            company_id,
            rol,
        )

        expected = {
            "exact_filters": {
                "company_id": company_id,
                "rol": rol,
            },
            "ilike_filters": {},
            "like_filters": {},
        }
        assert result == expected

    def test_obtener_filtros_no_parameters(self, super_admin_case, mock_usuario_actual):
        """Test obtener_filtros_para_listar_usuarios with no parameters."""
        result = super_admin_case.obtener_filtros_para_listar_usuarios(
            mock_usuario_actual,
            None,
            None,
            None,
        )

        expected = {
            "exact_filters": {},
            "ilike_filters": {},
            "like_filters": {},
        }
        assert result == expected

    def test_obtener_filtros_empty_strings(self, super_admin_case, mock_usuario_actual):
        """Test obtener_filtros_para_listar_usuarios with empty string parameters."""
        result = super_admin_case.obtener_filtros_para_listar_usuarios(
            mock_usuario_actual,
            "",
            "",
            "",
        )

        expected = {
            "exact_filters": {},
            "ilike_filters": {},
            "like_filters": {},
        }
        assert result == expected

    def test_obtener_filtros_whitespace_search(self, super_admin_case, mock_usuario_actual):
        """Test obtener_filtros_para_listar_usuarios with whitespace search."""
        search = "  john doe  "

        result = super_admin_case.obtener_filtros_para_listar_usuarios(
            mock_usuario_actual,
            search,
            None,
            None,
        )

        expected = {
            "exact_filters": {},
            "ilike_filters": {
                "display_name": f"%{search}%",
            },
            "like_filters": {},
        }
        assert result == expected

    @pytest.mark.parametrize("user_rol", [Rol.ADMIN, Rol.TECHNICIAN])
    def test_obtener_firebase_usuario_various_non_super_admin_roles(
        self,
        super_admin_case,
        usuario_create_data,
        mock_compania,
        mock_tipo_documento,
        user_rol,
    ):
        """Test that various non-super-admin roles are denied permission."""
        non_super_admin = Usuario(
            id=uuid4(),
            uid="user-uid",
            email="user@example.com",
            display_name="User",
            rol=user_rol,
            company_id=uuid4(),
        )

        params = CrearUsuarioFirebaseParams(
            usuario_actual=non_super_admin,
            usuario_nuevo=usuario_create_data,
            compania=mock_compania,
            tipo_documento=mock_tipo_documento,
            cliente=None,
        )

        with pytest.raises(HTTPException) as exc_info:
            super_admin_case.obtener_firebase_usuario(params)

        assert exc_info.value.status_code == 403

    @pytest.mark.parametrize("user_rol", [Rol.ADMIN, Rol.TECHNICIAN])
    def test_obtener_usuario_a_guardar_various_non_super_admin_roles(
        self,
        super_admin_case,
        usuario_create_data,
        user_rol,
    ):
        """Test that various non-super-admin roles are denied permission for user creation."""
        non_super_admin = Usuario(
            id=uuid4(),
            uid="user-uid",
            email="user@example.com",
            display_name="User",
            rol=user_rol,
            company_id=uuid4(),
        )

        params = CrearUsuarioParams(
            usuario_actual=non_super_admin,
            usuario_nuevo=usuario_create_data,
            firebase_uid="firebase-uid",
        )

        with pytest.raises(HTTPException) as exc_info:
            super_admin_case.obtener_usuario_a_guardar(params)

        assert exc_info.value.status_code == 403
