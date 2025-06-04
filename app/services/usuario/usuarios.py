# app/services/usuarios.py

from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy import select

from app.db.models.usuarios import Usuario
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate
from app.db.repositories.usuarios import usuario_crud

class UsuarioService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[Usuario]:
        return await usuario_crud.get_multi(self.db)

    async def get_by_uid(self, uid: str) -> Usuario:
        return await usuario_crud.get_by_field(self.db, "uid", uid)

    async def create(self, usuario_actual: Usuario, usuario_in: UsuarioCreate) -> Usuario:
        usuario = await usuario_crud.get_by_field(self.db, "uid", usuario_in.uid)
        if usuario:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario ya existe")
        return await usuario_crud.create(self.db, obj_in=usuario_in)

    async def update(self, uid: str, usuario_in: UsuarioUpdate) -> Usuario:
        usuario = await self.get_by_uid(uid)
        return await usuario_crud.update(self.db, db_obj=usuario, obj_in=usuario_in)

    async def delete(self, uid: str) -> Usuario:
        usuario = await self.get_by_uid(uid)
        return await usuario_crud.remove(self.db, db_obj=usuario)
