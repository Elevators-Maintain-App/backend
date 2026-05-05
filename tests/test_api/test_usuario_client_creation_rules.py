from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.db.models.usuarios import Rol
from app.services.usuario import usuarios as usuarios_service_module
from app.services.usuario.usuarios import UsuarioService


COMPANY_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_COMPANY_ID = UUID("22222222-2222-2222-2222-222222222222")
CLIENT_ID = UUID("33333333-3333-3333-3333-333333333333")


class DummyDB:
    pass


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

