# app/services/usuarios.py

from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy import select

from app.db.models.usuarios import Usuario
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate, UsuarioOut
from app.db.repositories.usuarios import usuario_crud
from app.services.compania import CompaniaService
from app.db.repositories.tipos_documento import tipo_documento_crud
from app.services.usuario.user_cases import FabricaDeUsuarios
from app.auth.firebase import crear_usuario_firebase

class UsuarioService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[UsuarioOut]:
        try:
            users = await usuario_crud.get_multi(self.db)
            return [UsuarioOut.model_validate(user) for user in users]
        except Exception as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener los usuarios")

    async def get_by_uid(self, uid: str) -> UsuarioOut:
        return await usuario_crud.get_by_field(self.db, "uid", uid)

    async def create(self, usuario_actual: Usuario, usuario_in: UsuarioCreate) -> UsuarioOut:
        usuario = await usuario_crud.get_by_field(self.db, "email", usuario_in.email)
        if usuario:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario ya existe")
    
        compania = await CompaniaService(self.db).get_compania(usuario_in.company_id)
        tipo_documento = await tipo_documento_crud.get(self.db, usuario_in.document_type_id)
        fabrica_de_usuarios = FabricaDeUsuarios.get_user_case(usuario_in.rol)
        usuario_firebase = fabrica_de_usuarios.obtener_firebase_usuario({
            "usuario_actual": usuario_actual,
            "usuario_nuevo": usuario_in,
            "compania": compania,
            "tipo_documento": tipo_documento
        })

        # crear usuario en firebase
        usuario_firebase = await crear_usuario_firebase(usuario_firebase)
        usuario_a_guardar: Usuario = None

        usuario_a_guardar = fabrica_de_usuarios.obtener_usuario_a_guardar({
                "usuario_actual": usuario_actual,
                "usuario_nuevo": usuario_in,
                "firebase_uid": usuario_firebase.uid
            })
        usuario_guardado = await usuario_crud.create(self.db, obj_in=usuario_a_guardar)

        return usuario_guardado
        
        

    async def update(self, uid: str, usuario_in: UsuarioUpdate) -> UsuarioOut:
        usuario = await self.get_by_uid(uid)
        return await usuario_crud.update(self.db, db_obj=usuario, obj_in=usuario_in)

    async def delete(self, uid: str) -> None:
        usuario = await self.get_by_uid(uid)
        return await usuario_crud.remove(self.db, db_obj=usuario)
