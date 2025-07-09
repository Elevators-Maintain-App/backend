import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from datetime import datetime

from app.services.usuario.usuarios import UsuarioService
from app.db.models.usuarios import Usuario, Rol
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate, UsuarioOut
from app.services.usuario.user_cases.super_admin import SuperAdminCase


class TestUsuarioService:
    """Test suite for UsuarioService class."""

    @pytest.fixture
    def usuario_service(self, mock_db_session):
        """Create a UsuarioService instance for testing."""
        return UsuarioService(mock_db_session)

    @pytest.fixture
    def usuario_create_data(self):
        """Create mock UsuarioCreate data."""
        return UsuarioCreate(
            email="newuser@example.com",
            display_name="New User",
            rol=Rol.ADMIN,
            company_id="12345678-1234-5678-9012-123456789abc",
            document_id="123456789",
            document_type_id=1,
            phone_number="+1234567890"
        )

    @pytest.fixture
    def usuario_update_data(self):
        """Create mock UsuarioUpdate data."""
        return UsuarioUpdate(
            display_name="Updated User Name",
            rol=Rol.TECHNICIAN
        )

    @pytest.mark.asyncio
    async def test_get_all_success(self, usuario_service, mock_usuario_actual, sample_usuarios_list):
        """Test successful get_all operation."""
        # Arrange
        with patch('app.services.usuario.usuarios.FabricaDeUsuarios.get_user_case') as mock_fabrica, \
             patch('app.services.usuario.usuarios.usuario_crud.get_usuarios_con_relaciones_con_paginacion') as mock_get_multi, \
             patch('app.services.usuario.usuarios.UsuarioService._total_usuarios_con_filtro') as mock_total:
            
            mock_case = MagicMock()
            mock_case.obtener_filtros_para_listar_usuarios.return_value = {
                "exact_filters": {"company_id": "123"},
                "ilike_filters": {"display_name": "%john%"},
                "like_filters": {}
            }
            mock_fabrica.return_value = mock_case
            mock_get_multi.return_value = sample_usuarios_list
            mock_total.return_value = len(sample_usuarios_list)

            # Act
            result = await usuario_service.get_usuarios_con_paginacion(
                usuario_actual=mock_usuario_actual,
                skip=0,
                limit=10,
                search="john",
                company_id="123",
                rol="ADMIN"
            )

            # Assert
            assert len(result.data) == len(sample_usuarios_list)
            assert result.total == len(sample_usuarios_list)
            mock_fabrica.assert_called_once_with(mock_usuario_actual.rol)
            mock_case.obtener_filtros_para_listar_usuarios.assert_called_once_with(
                mock_usuario_actual, "john", "123", "ADMIN"
            )
            mock_get_multi.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_no_filters(self, usuario_service, mock_usuario_actual, sample_usuarios_list):
        """Test get_all operation without filters."""
        # Arrange
        with patch('app.services.usuario.usuarios.FabricaDeUsuarios.get_user_case') as mock_fabrica, \
             patch('app.services.usuario.usuarios.usuario_crud.get_usuarios_con_relaciones_con_paginacion') as mock_get_multi, \
             patch('app.services.usuario.usuarios.UsuarioService._total_usuarios_con_filtro') as mock_total:
            
            mock_case = MagicMock()
            mock_case.obtener_filtros_para_listar_usuarios.return_value = {
                "exact_filters": {},
                "ilike_filters": {},
                "like_filters": {}
            }
            mock_fabrica.return_value = mock_case
            mock_get_multi.return_value = sample_usuarios_list
            mock_total.return_value = len(sample_usuarios_list)

            # Act
            result = await usuario_service.get_usuarios_con_paginacion(
                usuario_actual=mock_usuario_actual,
                skip=None,
                limit=None
            )

            # Assert
            assert len(result.data) == len(sample_usuarios_list)
            mock_case.obtener_filtros_para_listar_usuarios.assert_called_once_with(
                mock_usuario_actual, None, None, None
            )

    @pytest.mark.asyncio
    async def test_get_all_error_handling(self, usuario_service, mock_usuario_actual):
        """Test get_all operation error handling."""
        # Arrange
        with patch('app.services.usuario.usuarios.FabricaDeUsuarios.get_user_case') as mock_fabrica:
            mock_fabrica.side_effect = Exception("Database error")

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await usuario_service.get_usuarios_con_paginacion(
                    usuario_actual=mock_usuario_actual,
                    skip=0,
                    limit=10
                )
            
            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Error al obtener los usuarios" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_by_uid_success(self, usuario_service, mock_compania, mock_tipo_documento):
        """Test successful get_by_uid operation."""
        # Arrange
        expected_user = Usuario(
            id="12345678-1234-5678-9012-123456789001",
            uid="firebase-uid",
            email="user@example.com",
            display_name="Test User",
            rol=Rol.ADMIN,
            company_id="12345678-1234-5678-9012-123456789abc",
            document_id="12345",
            document_type_id=1,
            phone_number="+1234567890",
            is_active=True,
            created_at=datetime.now()
        )
        # Mock the relationships
        expected_user.company = mock_compania
        expected_user.document_type = mock_tipo_documento
        
        with patch('app.services.usuario.usuarios.usuario_crud.get_usuario_con_relaciones') as mock_get_user:
            mock_get_user.return_value = expected_user

            # Act
            result = await usuario_service.get_by_uid("firebase-uid")

            # Assert
            assert isinstance(result, UsuarioOut)
            assert result.company_name == mock_compania.nombre
            assert result.document_type_name == mock_tipo_documento.nombre
            mock_get_user.assert_called_once_with(
                usuario_service.db, "firebase-uid"
            )

    @pytest.mark.asyncio
    async def test_create_success(
        self, 
        usuario_service, 
        mock_usuario_actual, 
        usuario_create_data, 
        mock_compania, 
        mock_tipo_documento
    ):
        """Test successful user creation."""
        # Arrange
        mock_firebase_user = MagicMock()
        mock_firebase_user.uid = "new-firebase-uid"
        created_user = Usuario(
            id="new-user-id",
            uid="new-firebase-uid",
            email=usuario_create_data.email,
            display_name=usuario_create_data.display_name,
            rol=usuario_create_data.rol,
            company_id=usuario_create_data.company_id
        )

        with patch('app.services.usuario.usuarios.usuario_crud.get_by_field') as mock_get_by_field, \
             patch('app.services.usuario.usuarios.CompaniaService') as mock_compania_service, \
             patch('app.services.usuario.usuarios.tipo_documento_crud.get') as mock_tipo_doc_get, \
             patch('app.services.usuario.usuarios.FabricaDeUsuarios.get_user_case') as mock_fabrica, \
             patch('app.services.usuario.usuarios.crear_usuario_firebase') as mock_crear_firebase, \
             patch('app.services.usuario.usuarios.usuario_crud.create') as mock_create:

            # Setup mocks
            mock_get_by_field.return_value = None  # User doesn't exist
            
            # Mock CompaniaService instance and its async method
            mock_compania_service_instance = AsyncMock()
            mock_compania_service_instance.get_compania.return_value = mock_compania
            mock_compania_service.return_value = mock_compania_service_instance
            
            mock_tipo_doc_get.return_value = mock_tipo_documento
            
            mock_case = MagicMock()
            mock_case.obtener_firebase_usuario.return_value = mock_firebase_user
            mock_case.obtener_usuario_a_guardar.return_value = created_user
            mock_case.enviar_email_de_bienvenida = AsyncMock(return_value=None)
            mock_fabrica.return_value = mock_case
            
            mock_crear_firebase.return_value = mock_firebase_user
            mock_create.return_value = created_user

            # Act
            result = await usuario_service.create(mock_usuario_actual, usuario_create_data)

            # Assert
            assert result == created_user
            mock_get_by_field.assert_called_once_with(
                usuario_service.db, "email", usuario_create_data.email
            )
            mock_crear_firebase.assert_called_once_with(mock_firebase_user)
            mock_create.assert_called_once_with(usuario_service.db, obj_in=created_user)

    @pytest.mark.asyncio
    async def test_create_user_already_exists(self, usuario_service, mock_usuario_actual, usuario_create_data):
        """Test user creation when user already exists."""
        # Arrange
        existing_user = Usuario(
            id="existing-user-id",
            uid="existing-firebase-uid",
            email=usuario_create_data.email,
            display_name="Existing User",
            rol=Rol.ADMIN,
            company_id="company-id"
        )

        with patch('app.services.usuario.usuarios.usuario_crud.get_by_field') as mock_get_by_field:
            mock_get_by_field.return_value = existing_user

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await usuario_service.create(mock_usuario_actual, usuario_create_data)
            
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "El usuario ya existe" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_success(self, usuario_service, usuario_update_data):
        """Test successful user update."""
        # Arrange
        uid = "firebase-uid"
        existing_user = Usuario(
            id="user-id",
            uid=uid,
            email="user@example.com",
            display_name="Original Name",
            rol=Rol.ADMIN,
            company_id="company-id"
        )
        updated_user = Usuario(
            id="user-id",
            uid=uid,
            email="user@example.com",
            display_name="Updated User Name",
            rol=Rol.TECHNICIAN,
            company_id="company-id"
        )

        with patch.object(usuario_service, 'get_by_uid') as mock_get_by_uid, \
             patch('app.services.usuario.usuarios.usuario_crud.update') as mock_update:
            
            mock_get_by_uid.return_value = existing_user
            mock_update.return_value = updated_user

            # Act
            result = await usuario_service.update(uid, usuario_update_data)

            # Assert
            assert result == updated_user
            mock_get_by_uid.assert_called_once_with(uid)
            mock_update.assert_called_once_with(
                usuario_service.db, db_obj=existing_user, obj_in=usuario_update_data
            )

    @pytest.mark.asyncio
    async def test_delete_success(self, usuario_service):
        """Test successful user deletion."""
        # Arrange
        uid = "firebase-uid"
        existing_user = Usuario(
            id="user-id",
            uid=uid,
            email="user@example.com",
            display_name="User to Delete",
            rol=Rol.ADMIN,
            company_id="company-id"
        )

        with patch.object(usuario_service, 'get_by_uid') as mock_get_by_uid, \
             patch('app.services.usuario.usuarios.usuario_crud.remove') as mock_remove:
            
            mock_get_by_uid.return_value = existing_user
            mock_remove.return_value = existing_user

            # Act
            result = await usuario_service.delete(uid)

            # Assert
            assert result == existing_user
            mock_get_by_uid.assert_called_once_with(uid)
            mock_remove.assert_called_once_with(usuario_service.db, db_obj=existing_user)

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, usuario_service, mock_usuario_actual, sample_usuarios_list):
        """Test get_all with pagination parameters."""
        # Arrange
        with patch('app.services.usuario.usuarios.FabricaDeUsuarios.get_user_case') as mock_fabrica, \
             patch('app.services.usuario.usuarios.usuario_crud.get_usuarios_con_relaciones_con_paginacion') as mock_get_multi, \
             patch('app.services.usuario.usuarios.UsuarioService._total_usuarios_con_filtro') as mock_total:
            
            mock_case = MagicMock()
            mock_case.obtener_filtros_para_listar_usuarios.return_value = {
                "exact_filters": {},
                "ilike_filters": {},
                "like_filters": {}
            }
            mock_fabrica.return_value = mock_case
            mock_get_multi.return_value = sample_usuarios_list[1:2]  # Simulate pagination
            mock_total.return_value = len(sample_usuarios_list)

            # Act
            result = await usuario_service.get_usuarios_con_paginacion(
                usuario_actual=mock_usuario_actual,
                skip=1,
                limit=1
            )

            # Assert
            assert len(result.data) == 1
            assert result.total == len(sample_usuarios_list)
            mock_get_multi.assert_called_once_with(
                usuario_service.db,
                skip=1,
                limit=1,
                exact_filters={},
                ilike_filters={},
                like_filters={}
            ) 