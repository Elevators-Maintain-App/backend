from types import SimpleNamespace
from datetime import datetime, timezone
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.auth.firebase import FirebaseUser, FirebaseUserCreationError, UsuarioFirebaseCreate
from app.db.models.usuarios import Rol
from app.services.usuario import usuarios as usuarios_service_module
from app.services.usuario.usuarios import UsuarioService


COMPANY_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_COMPANY_ID = UUID("22222222-2222-2222-2222-222222222222")
CLIENT_ID = UUID("33333333-3333-3333-3333-333333333333")
USER_ID = UUID("44444444-4444-4444-4444-444444444444")
NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class DummyDB:
    pass


def make_current_user():
    return SimpleNamespace(uid="superadmin", rol=Rol.SUPER_ADMIN, company_id=COMPANY_ID)


def make_usuario(uid="firebase-created-uid", email="nuevo@example.invalid", client_id=CLIENT_ID):
    return SimpleNamespace(
        id=USER_ID,
        uid=uid,
        company_id=COMPANY_ID,
        company=SimpleNamespace(nombre="Compania"),
        display_name="Usuario Nuevo",
        document_id="DOC-1",
        document_type_id=1,
        document_type=SimpleNamespace(nombre="Cedula"),
        email=email,
        phone_number="+50700000000",
        rol=Rol.CLIENT,
        client_id=client_id,
        client=SimpleNamespace(nombre="Cliente"),
        nivel=None,
        zona_geografica_id=None,
        photo_url=None,
        is_active=True,
        created_at=NOW,
        updated_at=NOW,
    )


class FakeUsuarioCase:
    sent_welcome_emails = []

    def validar_y_normalizar_company_id(self, usuario_actual, company_id):
        return company_id

    def obtener_firebase_usuario(self, params):
        return UsuarioFirebaseCreate(
            company_id=params.compania.id,
            company_name=params.compania.nombre,
            client_id=params.cliente.id if params.cliente else None,
            client_name=params.cliente.nombre if params.cliente else None,
            display_name=params.usuario_nuevo.display_name,
            document_id=params.usuario_nuevo.document_id,
            document_type=str(params.tipo_documento.id),
            document_type_name=params.tipo_documento.nombre,
            email=params.usuario_nuevo.email,
            photo_url=params.usuario_nuevo.photo_url,
            rol=params.usuario_nuevo.rol,
        )

    def obtener_usuario_a_guardar(self, params):
        return make_usuario(
            uid=params.firebase_uid,
            email=params.usuario_nuevo.email,
            client_id=params.usuario_nuevo.client_id,
        )

    async def enviar_email_de_bienvenida(self, email_destinatario, nombre_destinatario, password):
        self.sent_welcome_emails.append(
            {
                "email": email_destinatario,
                "nombre": nombre_destinatario,
                "password": password,
            }
        )


def install_create_user_fakes(monkeypatch, *, postgres_user=None, postgres_user_by_uid=None):
    state = SimpleNamespace(
        created_auth=[],
        recovered_auth=[],
        firestore_updates=[],
        postgres_created=[],
        case=FakeUsuarioCase(),
    )
    FakeUsuarioCase.sent_welcome_emails = []

    async def fake_get_compania(self, company_id, usuario_actual):
        return SimpleNamespace(id=company_id, nombre="Compania")

    async def fake_get_tipo_documento(db, document_type_id):
        return SimpleNamespace(id=document_type_id, nombre="Cedula")

    async def fake_get_cliente(db, field, value):
        return SimpleNamespace(id=value, nombre="Cliente", compania_id=COMPANY_ID)

    class FakeUsuarioCrud:
        async def get_by_field(self, db, field, value):
            if field == "email":
                return postgres_user
            return None

        async def get_usuario_con_relaciones(self, db, uid):
            if postgres_user_by_uid and postgres_user_by_uid.uid == uid:
                return postgres_user_by_uid
            for usuario in state.postgres_created:
                if usuario.uid == uid:
                    return usuario
            return None

        async def create(self, db, obj_in):
            state.postgres_created.append(obj_in)
            return obj_in

    async def fake_crear_usuario_firebase(usuario_firebase):
        state.created_auth.append(usuario_firebase.email)
        return FirebaseUser(
            uid="firebase-created-uid",
            email=usuario_firebase.email,
            display_name=usuario_firebase.display_name,
            created_time=NOW,
            company_id=usuario_firebase.company_id,
            company_name=usuario_firebase.company_name,
            document_id=usuario_firebase.document_id,
            document_type=usuario_firebase.document_type,
            document_type_name=usuario_firebase.document_type_name,
            photo_url=usuario_firebase.photo_url,
            rol=usuario_firebase.rol,
            client_id=usuario_firebase.client_id,
            client_name=usuario_firebase.client_name,
            password="temporary-password",
        )

    async def fake_obtener_usuario_firebase_por_email(usuario_firebase):
        state.recovered_auth.append(usuario_firebase.email)
        return FirebaseUser(
            uid="firebase-existing-uid",
            email=usuario_firebase.email,
            display_name=usuario_firebase.display_name,
            created_time=NOW,
            company_id=usuario_firebase.company_id,
            company_name=usuario_firebase.company_name,
            document_id=usuario_firebase.document_id,
            document_type=usuario_firebase.document_type,
            document_type_name=usuario_firebase.document_type_name,
            photo_url=usuario_firebase.photo_url,
            rol=usuario_firebase.rol,
            client_id=usuario_firebase.client_id,
            client_name=usuario_firebase.client_name,
            password=None,
        )

    async def fake_actualizar_usuario_firestore(uid, data):
        state.firestore_updates.append((uid, data))
        return True

    monkeypatch.setattr(
        usuarios_service_module.FabricaDeUsuarios,
        "get_user_case",
        lambda rol: state.case,
    )
    monkeypatch.setattr(usuarios_service_module, "CompaniaService", lambda db: SimpleNamespace(get_compania=fake_get_compania.__get__(object())))
    monkeypatch.setattr(usuarios_service_module.tipo_documento_crud, "get", fake_get_tipo_documento)
    monkeypatch.setattr(usuarios_service_module.cliente_crud, "get_by_field", fake_get_cliente)
    monkeypatch.setattr(usuarios_service_module, "usuario_crud", FakeUsuarioCrud())
    monkeypatch.setattr(usuarios_service_module, "crear_usuario_firebase", fake_crear_usuario_firebase)
    monkeypatch.setattr(usuarios_service_module, "obtener_usuario_firebase_por_email", fake_obtener_usuario_firebase_por_email)
    monkeypatch.setattr(usuarios_service_module, "actualizar_usuario_firestore", fake_actualizar_usuario_firestore)
    return state


def valid_client_user_payload(email="nuevo@example.invalid", client_id=CLIENT_ID):
    return {
        "company_id": COMPANY_ID,
        "display_name": "Usuario Nuevo",
        "document_id": "DOC-1",
        "document_type_id": 1,
        "email": email,
        "phone_number": "+50700000000",
        "rol": Rol.CLIENT,
        "client_id": client_id,
        "is_active": True,
    }


@pytest.mark.asyncio
async def test_client_user_requires_client_id():
    service = UsuarioService(DummyDB())

    with pytest.raises(HTTPException) as exc_info:
        await service._get_cliente_para_usuario_client(
            rol=Rol.CLIENT,
            client_id=None,
            company_id=COMPANY_ID,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "El client_id es requerido para usuarios client"


@pytest.mark.asyncio
async def test_client_user_requires_existing_client(monkeypatch):
    async def fake_get_by_field(db, field, value):
        assert field == "id"
        assert value == CLIENT_ID
        return None

    monkeypatch.setattr(
        usuarios_service_module.cliente_crud,
        "get_by_field",
        fake_get_by_field,
    )
    service = UsuarioService(DummyDB())

    with pytest.raises(HTTPException) as exc_info:
        await service._get_cliente_para_usuario_client(
            rol=Rol.CLIENT,
            client_id=CLIENT_ID,
            company_id=COMPANY_ID,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "El cliente no existe"


@pytest.mark.asyncio
async def test_client_user_requires_client_from_same_company(monkeypatch):
    async def fake_get_by_field(db, field, value):
        return SimpleNamespace(id=value, compania_id=OTHER_COMPANY_ID)

    monkeypatch.setattr(
        usuarios_service_module.cliente_crud,
        "get_by_field",
        fake_get_by_field,
    )
    service = UsuarioService(DummyDB())

    with pytest.raises(HTTPException) as exc_info:
        await service._get_cliente_para_usuario_client(
            rol=Rol.CLIENT,
            client_id=CLIENT_ID,
            company_id=COMPANY_ID,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "El cliente no pertenece a la compania del usuario"


@pytest.mark.asyncio
async def test_non_client_user_does_not_require_client_id(monkeypatch):
    async def fail_if_called(db, field, value):
        raise AssertionError("No debe consultar clientes para roles no client")

    monkeypatch.setattr(
        usuarios_service_module.cliente_crud,
        "get_by_field",
        fail_if_called,
    )
    service = UsuarioService(DummyDB())

    cliente = await service._get_cliente_para_usuario_client(
        rol=Rol.ADMIN,
        client_id=None,
        company_id=COMPANY_ID,
    )

    assert cliente is None


@pytest.mark.asyncio
async def test_new_user_creates_auth_firestore_and_postgres(monkeypatch):
    state = install_create_user_fakes(monkeypatch)
    service = UsuarioService(DummyDB())

    usuario = await service.create(
        make_current_user(),
        valid_client_user_payload(email="Nuevo@Example.Invalid"),
        request_id="create-new-user",
    )

    assert usuario.uid == "firebase-created-uid"
    assert usuario.email == "nuevo@example.invalid"
    assert usuario.client_id == CLIENT_ID
    assert state.created_auth == ["nuevo@example.invalid"]
    assert state.recovered_auth == []
    assert state.postgres_created[0].uid == "firebase-created-uid"
    assert state.firestore_updates[0][0] == "firebase-created-uid"
    assert FakeUsuarioCase.sent_welcome_emails


@pytest.mark.asyncio
async def test_existing_firebase_without_postgres_recovers_and_creates_postgres(monkeypatch):
    state = install_create_user_fakes(monkeypatch)

    async def fake_crear_usuario_firebase(usuario_firebase):
        raise FirebaseUserCreationError(
            "El usuario con el email ya existe",
            error_code="EMAIL_ALREADY_EXISTS",
        )

    monkeypatch.setattr(usuarios_service_module, "crear_usuario_firebase", fake_crear_usuario_firebase)
    service = UsuarioService(DummyDB())

    usuario = await service.create(
        make_current_user(),
        valid_client_user_payload(email="recuperar@example.invalid"),
        request_id="recover-auth-user",
    )

    assert usuario.uid == "firebase-existing-uid"
    assert state.recovered_auth == ["recuperar@example.invalid"]
    assert state.postgres_created[0].uid == "firebase-existing-uid"
    assert state.firestore_updates[0][0] == "firebase-existing-uid"
    assert FakeUsuarioCase.sent_welcome_emails == []


@pytest.mark.asyncio
async def test_postgres_existing_user_returns_real_duplicate_and_syncs_firestore(monkeypatch):
    existing_user = make_usuario(uid="postgres-existing-uid", email="duplicado@example.invalid")
    state = install_create_user_fakes(
        monkeypatch,
        postgres_user=existing_user,
        postgres_user_by_uid=existing_user,
    )
    service = UsuarioService(DummyDB())

    with pytest.raises(HTTPException) as exc_info:
        await service.create(
            make_current_user(),
            valid_client_user_payload(email="duplicado@example.invalid"),
            request_id="duplicate-user",
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "El usuario ya existe en VertiOne"
    assert state.created_auth == []
    assert state.postgres_created == []
    assert state.firestore_updates[0][0] == "postgres-existing-uid"


@pytest.mark.asyncio
async def test_client_user_with_valid_client_id_creates_ok(monkeypatch):
    state = install_create_user_fakes(monkeypatch)
    service = UsuarioService(DummyDB())

    usuario = await service.create(
        make_current_user(),
        valid_client_user_payload(),
        request_id="client-valid",
    )

    assert usuario.client_id == CLIENT_ID
    assert state.postgres_created[0].client_id == CLIENT_ID


@pytest.mark.asyncio
async def test_client_user_with_client_from_other_company_fails_on_create(monkeypatch):
    install_create_user_fakes(monkeypatch)

    async def fake_get_cliente(db, field, value):
        return SimpleNamespace(id=value, nombre="Otro cliente", compania_id=OTHER_COMPANY_ID)

    monkeypatch.setattr(usuarios_service_module.cliente_crud, "get_by_field", fake_get_cliente)
    service = UsuarioService(DummyDB())

    with pytest.raises(HTTPException) as exc_info:
        await service.create(
            make_current_user(),
            valid_client_user_payload(),
            request_id="client-other-company",
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "El cliente no pertenece a la compania del usuario"
