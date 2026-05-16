import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from uuid import uuid4

from app.services.usuario.usuarios import UsuarioService
from app.db.models.usuarios import Usuario, Rol
from app.schemas.usuarios import UsuarioUpdate


class TestUsuarioService:
    """Test suite for UsuarioService class."""

    @pytest.fixture
    def usuario_service(self, mock_db_session):
        """Create a UsuarioService instance for testing."""
        return UsuarioService(mock_db_session)

    @pytest.fixture
    def usuario_create_data(self):
        """Create valid UsuarioCreate-compatible dict data."""
        return {
            "email": "newuser@example.com",
            "display_name": "New User",
            "rol": Rol.ADMIN,
            "company_id": uuid4(),
            "document_type_id": 1,
            "document_id": "123456789",
            "phone_number": "6000-0000",
        }

    @pytest.fixture
    def usuario_update_data(self):
        """Create mock UsuarioUpdate data."""
        return UsuarioUpdate(
            display_name="Updated User Name",
            rol=Rol.TECHNICIAN,
        )

    @pytest.fixture
    def expected_user_out(self):
        """Simple object used as mapper output in tests."""
        return MagicMock(name="UsuarioOutMock")

    @pytest.mark.asyncio
    async def test_get_all_success(self, usuario_service, mock_usuario_actual, sample_usuarios_list):
        """Test successful get_usuarios_con_paginacion operation."""
        with patch("app.services.usuario.usuarios.FabricaDeUsuarios.get_user_case") as mock_fabrica, \
             patch("app.services.usuario.usuarios.usuario_crud.get_usuarios_con_relaciones_con_paginacion") as mock_get_users, \
             patch("app.services.usuario.usuarios.usuario_crud.get_total_with_advanced_filters") as mock_get_total, \
             patch("app.services.usuario.usuarios.usuarios_to_usuarios_out") as mock_mapper:

            mock_case = MagicMock()
            mock_case.obtener_filtros_para_listar_usuarios.return_value = {
                "exact_filters": {"company_id": "123"},
                "ilike_filters": {"display_name": "%john%"},
                "like_filters": {},
            }
            mock_fabrica.return_value = mock_case
            mock_get_users.return_value = sample_usuarios_list
            mock_get_total.return_value = len(sample_usuarios_list)
            mock_mapper.return_value = sample_usuarios_list

            result = await usuario_service.get_usuarios_con_paginacion(
                usuario_actual=mock_usuario_actual,
                skip=0,
                limit=10,
                search="john",
                company_id="123",
                rol="ADMIN",
            )

            assert result.data == sample_usuarios_list
            assert result.total == len(sample_usuarios_list)
            assert result.skip == 0
            assert result.limit == 10
            mock_fabrica.assert_called_once_with(mock_usuario_actual.rol)
            mock_case.obtener_filtros_para_listar_usuarios.assert_called_once_with(
                mock_usuario_actual,
                "john",
                "123",
                "ADMIN",
            )
            mock_get_users.assert_called_once_with(
                usuario_service.db,
                skip=0,
                limit=10,
                exact_filters={"company_id": "123"},
                ilike_filters={"display_name": "%john%"},
                like_filters={},
            )
            mock_get_total.assert_called_once_with(
                usuario_service.db,
                exact_filters={"company_id": "123"},
                ilike_filters={"display_name": "%john%"},
                like_filters={},
            )

    @pytest.mark.asyncio
    async def test_get_all_no_filters(self, usuario_service, mock_usuario_actual, sample_usuarios_list):
        """Test get_usuarios_con_paginacion operation without filters."""
        with patch("app.services.usuario.usuarios.FabricaDeUsuarios.get_user_case") as mock_fabrica, \
             patch("app.services.usuario.usuarios.usuario_crud.get_usuarios_con_relaciones_con_paginacion") as mock_get_users, \
             patch("app.services.usuario.usuarios.usuario_crud.get_total_with_advanced_filters") as mock_get_total, \
             patch("app.services.usuario.usuarios.usuarios_to_usuarios_out") as mock_mapper:

            mock_case = MagicMock()
            mock_case.obtener_filtros_para_listar_usuarios.return_value = {
                "exact_filters": {},
                "ilike_filters": {},
                "like_filters": {},
            }
            mock_fabrica.return_value = mock_case
            mock_get_users.return_value = sample_usuarios_list
            mock_get_total.return_value = len(sample_usuarios_list)
            mock_mapper.return_value = sample_usuarios_list

            result = await usuario_service.get_usuarios_con_paginacion(
                usuario_actual=mock_usuario_actual,
                skip=0,
                limit=10,
            )

            assert result.data == sample_usuarios_list
            assert result.total == len(sample_usuarios_list)
            mock_case.obtener_filtros_para_listar_usuarios.assert_called_once_with(
                mock_usuario_actual,
                None,
                None,
                None,
            )

    @pytest.mark.asyncio
    async def test_get_all_error_handling(self, usuario_service, mock_usuario_actual):
        """Test get_usuarios_con_paginacion error handling."""
        with patch("app.services.usuario.usuarios.FabricaDeUsuarios.get_user_case") as mock_fabrica:
            mock_fabrica.side_effect = Exception("Database error")

            with pytest.raises(HTTPException) as exc_info:
                await usuario_service.get_usuarios_con_paginacion(
                    usuario_actual=mock_usuario_actual,
                    skip=0,
                    limit=10,
                )

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Error al obtener los usuarios" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_by_uid_success(self, usuario_service, expected_user_out):
        """Test successful get_by_uid operation."""
        expected_user = Usuario(
            id="user-id",
            uid="firebase-uid",
            email="user@example.com",
            display_name="Test User",
            rol=Rol.ADMIN,
            company_id=uuid4(),
        )

        with patch("app.services.usuario.usuarios.usuario_crud.get_usuario_con_relaciones") as mock_get_usuario, \
             patch("app.services.usuario.usuarios.usuario_to_usuario_out") as mock_mapper:

            mock_get_usuario.return_value = expected_user
            mock_mapper.return_value = expected_user_out

            result = await usuario_service.get_by_uid("firebase-uid")

            assert result == expected_user_out
            mock_get_usuario.assert_called_once_with(usuario_service.db, "firebase-uid")
            mock_mapper.assert_called_once_with(expected_user)

    @pytest.mark.asyncio
    async def test_get_by_uid_not_found(self, usuario_service):
        """Test get_by_uid when user does not exist."""
        with patch("app.services.usuario.usuarios.usuario_crud.get_usuario_con_relaciones") as mock_get_usuario:
            mock_get_usuario.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await usuario_service.get_by_uid("missing-uid")

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "Usuario no encontrado" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_success(
        self,
        usuario_service,
        mock_usuario_actual,
        usuario_create_data,
        mock_compania,
        mock_tipo_documento,
    ):
        """Test successful user creation with current service flow."""
        mock_firebase_user = MagicMock()
        mock_firebase_user.uid = "new-firebase-uid"
        mock_firebase_user.password = "Temp12345"

        created_user = Usuario(
            id="new-user-id",
            uid="new-firebase-uid",
            email=usuario_create_data["email"],
            display_name=usuario_create_data["display_name"],
            rol=usuario_create_data["rol"],
            company_id=usuario_create_data["company_id"],
            document_type_id=usuario_create_data["document_type_id"],
            document_id=usuario_create_data["document_id"],
            phone_number=usuario_create_data["phone_number"],
        )

        with patch("app.services.usuario.usuarios.usuario_crud.get_by_field") as mock_get_by_field, \
             patch("app.services.usuario.usuarios.CompaniaService") as mock_compania_service, \
             patch("app.services.usuario.usuarios.tipo_documento_crud.get") as mock_tipo_doc_get, \
             patch("app.services.usuario.usuarios.FabricaDeUsuarios.get_user_case") as mock_fabrica, \
             patch.object(usuario_service, "_crear_o_recuperar_usuario_firebase") as mock_firebase, \
             patch("app.services.usuario.usuarios.usuario_crud.get_usuario_con_relaciones") as mock_get_relaciones, \
             patch("app.services.usuario.usuarios.usuario_crud.create") as mock_create, \
             patch("app.services.usuario.usuarios.PlanEnforcementService") as mock_plan_service, \
             patch.object(usuario_service, "_sync_usuario_firestore") as mock_sync_firestore, \
             patch("app.services.usuario.usuarios.usuario_to_usuario_out") as mock_mapper:

            mock_get_by_field.return_value = None
            mock_compania_service.return_value.get_compania = AsyncMock(return_value=mock_compania)
            mock_tipo_doc_get.return_value = mock_tipo_documento

            mock_case = MagicMock()
            mock_case.validar_y_normalizar_company_id.return_value = usuario_create_data["company_id"]
            mock_case.obtener_firebase_usuario.return_value = MagicMock()
            mock_case.obtener_usuario_a_guardar.return_value = created_user
            mock_case.enviar_email_de_bienvenida = AsyncMock()
            mock_fabrica.return_value = mock_case

            mock_plan_service.return_value.assert_can_create_user = AsyncMock()
            mock_plan_service.return_value.refresh_current_usage_snapshot = AsyncMock()

            mock_firebase.return_value = (mock_firebase_user, True)
            mock_get_relaciones.side_effect = [None, created_user]
            mock_create.return_value = created_user
            mock_sync_firestore.return_value = None
            mock_mapper.return_value = created_user

            result = await usuario_service.create(mock_usuario_actual, usuario_create_data)

            assert result == created_user
            mock_case.validar_y_normalizar_company_id.assert_called_once_with(
                mock_usuario_actual,
                usuario_create_data["company_id"],
            )
            mock_plan_service.return_value.assert_can_create_user.assert_called_once_with(
                usuario_create_data["company_id"],
                usuario_create_data["rol"],
            )
            mock_create.assert_called_once_with(usuario_service.db, obj_in=created_user)
            mock_plan_service.return_value.refresh_current_usage_snapshot.assert_called_once_with(
                created_user.company_id,
            )
            mock_sync_firestore.assert_called_once_with(created_user)
            mock_case.enviar_email_de_bienvenida.assert_called_once_with(
                created_user.email,
                created_user.display_name,
                mock_firebase_user.password,
            )

    @pytest.mark.asyncio
    async def test_create_returns_success_when_firestore_sync_fails_after_postgres_create(
        self,
        usuario_service,
        mock_usuario_actual,
        usuario_create_data,
        mock_compania,
        mock_tipo_documento,
    ):
        """Regression test: Firestore sync failure after DB creation must not break response."""
        mock_firebase_user = MagicMock()
        mock_firebase_user.uid = "new-firebase-uid"
        mock_firebase_user.password = "Temp12345"

        created_user = Usuario(
            id="new-user-id",
            uid="new-firebase-uid",
            email=usuario_create_data["email"],
            display_name=usuario_create_data["display_name"],
            rol=usuario_create_data["rol"],
            company_id=usuario_create_data["company_id"],
            document_type_id=usuario_create_data["document_type_id"],
            document_id=usuario_create_data["document_id"],
            phone_number=usuario_create_data["phone_number"],
        )

        with patch("app.services.usuario.usuarios.usuario_crud.get_by_field") as mock_get_by_field, \
             patch("app.services.usuario.usuarios.CompaniaService") as mock_compania_service, \
             patch("app.services.usuario.usuarios.tipo_documento_crud.get") as mock_tipo_doc_get, \
             patch("app.services.usuario.usuarios.FabricaDeUsuarios.get_user_case") as mock_fabrica, \
             patch.object(usuario_service, "_crear_o_recuperar_usuario_firebase") as mock_firebase, \
             patch("app.services.usuario.usuarios.usuario_crud.get_usuario_con_relaciones") as mock_get_relaciones, \
             patch("app.services.usuario.usuarios.usuario_crud.create") as mock_create, \
             patch("app.services.usuario.usuarios.PlanEnforcementService") as mock_plan_service, \
             patch.object(usuario_service, "_sync_usuario_firestore") as mock_sync_firestore, \
             patch("app.services.usuario.usuarios.usuario_to_usuario_out") as mock_mapper:

            mock_get_by_field.return_value = None
            mock_compania_service.return_value.get_compania = AsyncMock(return_value=mock_compania)
            mock_tipo_doc_get.return_value = mock_tipo_documento

            mock_case = MagicMock()
            mock_case.validar_y_normalizar_company_id.return_value = usuario_create_data["company_id"]
            mock_case.obtener_firebase_usuario.return_value = MagicMock()
            mock_case.obtener_usuario_a_guardar.return_value = created_user
            mock_case.enviar_email_de_bienvenida = AsyncMock()
            mock_fabrica.return_value = mock_case

            mock_plan_service.return_value.assert_can_create_user = AsyncMock()
            mock_plan_service.return_value.refresh_current_usage_snapshot = AsyncMock()

            mock_firebase.return_value = (mock_firebase_user, True)
            mock_get_relaciones.side_effect = [None, created_user]
            mock_create.return_value = created_user
            mock_sync_firestore.side_effect = Exception("Firestore unavailable")
            mock_mapper.return_value = created_user

            result = await usuario_service.create(mock_usuario_actual, usuario_create_data)

            assert result == created_user
            mock_create.assert_called_once_with(usuario_service.db, obj_in=created_user)
            mock_sync_firestore.assert_called_once_with(created_user)
            mock_case.enviar_email_de_bienvenida.assert_called_once_with(
                created_user.email,
                created_user.display_name,
                mock_firebase_user.password,
            )

    @pytest.mark.asyncio
    async def test_create_user_already_exists(self, usuario_service, mock_usuario_actual, usuario_create_data):
        """Test user creation when user already exists."""
        existing_user = Usuario(
            id="existing-user-id",
            uid="existing-firebase-uid",
            email=usuario_create_data["email"],
            display_name="Existing User",
            rol=Rol.ADMIN,
            company_id=usuario_create_data["company_id"],
        )

        with patch("app.services.usuario.usuarios.usuario_crud.get_by_field") as mock_get_by_field, \
             patch("app.services.usuario.usuarios.FabricaDeUsuarios.get_user_case") as mock_fabrica, \
             patch("app.services.usuario.usuarios.usuario_crud.get_usuario_con_relaciones") as mock_get_relaciones, \
             patch.object(usuario_service, "_sync_usuario_firestore") as mock_sync_firestore:

            mock_case = MagicMock()
            mock_case.validar_y_normalizar_company_id.return_value = usuario_create_data["company_id"]
            mock_fabrica.return_value = mock_case

            mock_get_by_field.return_value = existing_user
            mock_get_relaciones.return_value = existing_user
            mock_sync_firestore.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await usuario_service.create(mock_usuario_actual, usuario_create_data)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "El usuario ya existe" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_success(self, usuario_service, usuario_update_data):
        """Test successful user update."""
        uid = "firebase-uid"
        existing_user = Usuario(
            id="user-id",
            uid=uid,
            email="user@example.com",
            display_name="Original Name",
            rol=Rol.ADMIN,
            company_id=uuid4(),
        )
        updated_user = Usuario(
            id="user-id",
            uid=uid,
            email="user@example.com",
            display_name="Updated User Name",
            rol=Rol.TECHNICIAN,
            company_id=existing_user.company_id,
        )
        expected_user_out = MagicMock(name="UpdatedUsuarioOut")

        with patch("app.services.usuario.usuarios.usuario_crud.get_usuario_con_relaciones") as mock_get_usuario, \
             patch("app.services.usuario.usuarios.usuario_crud.update") as mock_update, \
             patch.object(usuario_service, "_get_cliente_para_usuario_client") as mock_get_cliente, \
             patch.object(usuario_service, "_sync_usuario_firestore") as mock_sync_firestore, \
             patch("app.services.usuario.usuarios.usuario_to_usuario_out") as mock_mapper:

            mock_get_usuario.side_effect = [existing_user, updated_user]
            mock_update.return_value = updated_user
            mock_get_cliente.return_value = None
            mock_sync_firestore.return_value = None
            mock_mapper.return_value = expected_user_out

            result = await usuario_service.update(uid, usuario_update_data)

            assert result == expected_user_out
            mock_get_usuario.assert_any_call(usuario_service.db, uid)
            mock_update.assert_called_once_with(
                usuario_service.db,
                db_obj=existing_user,
                obj_in=usuario_update_data,
            )
            mock_sync_firestore.assert_called_once_with(updated_user)
            mock_mapper.assert_called_once_with(updated_user)

    @pytest.mark.asyncio
    async def test_delete_success(self, usuario_service):
        """Test successful user deletion."""
        uid = "firebase-uid"
        existing_user = MagicMock(name="UsuarioOutOrModel")

        with patch.object(usuario_service, "get_by_uid") as mock_get_by_uid, \
             patch("app.services.usuario.usuarios.usuario_crud.remove") as mock_remove:

            mock_get_by_uid.return_value = existing_user
            mock_remove.return_value = existing_user

            result = await usuario_service.delete(uid)

            assert result == existing_user
            mock_get_by_uid.assert_called_once_with(uid)
            mock_remove.assert_called_once_with(usuario_service.db, db_obj=existing_user)

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, usuario_service, mock_usuario_actual, sample_usuarios_list):
        """Test get_usuarios_con_paginacion with pagination parameters."""
        paginated_users = sample_usuarios_list[1:2]

        with patch("app.services.usuario.usuarios.FabricaDeUsuarios.get_user_case") as mock_fabrica, \
             patch("app.services.usuario.usuarios.usuario_crud.get_usuarios_con_relaciones_con_paginacion") as mock_get_users, \
             patch("app.services.usuario.usuarios.usuario_crud.get_total_with_advanced_filters") as mock_get_total, \
             patch("app.services.usuario.usuarios.usuarios_to_usuarios_out") as mock_mapper:

            mock_case = MagicMock()
            mock_case.obtener_filtros_para_listar_usuarios.return_value = {
                "exact_filters": {},
                "ilike_filters": {},
                "like_filters": {},
            }
            mock_fabrica.return_value = mock_case
            mock_get_users.return_value = paginated_users
            mock_get_total.return_value = len(sample_usuarios_list)
            mock_mapper.return_value = paginated_users

            result = await usuario_service.get_usuarios_con_paginacion(
                usuario_actual=mock_usuario_actual,
                skip=1,
                limit=1,
            )

            assert result.data == paginated_users
            assert result.total == len(sample_usuarios_list)
            assert result.skip == 1
            assert result.limit == 1
            mock_get_users.assert_called_once_with(
                usuario_service.db,
                skip=1,
                limit=1,
                exact_filters={},
                ilike_filters={},
                like_filters={},
            )
