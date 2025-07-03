from fastapi import HTTPException
from app.db.models.compania import Compania
from app.db.models import TipoDocumento
from app.db.models.usuarios import Usuario, Rol
from app.schemas.usuarios import UsuarioCreate
from app.auth.firebase import FirebaseUser
from .utils import mapear_usuario_dto_a_usuario_firebase, mapear_usuario_dto_a_usuario_create
from app.services.usuario.interfaces import UsuarioCaseInterface, CrearUsuarioFirebaseParams, CrearUsuarioParams
from typing import Optional
from uuid import UUID

VERTIONE_COMPANY_ID = "00000000-0000-0000-0000-000000000000"
VERTIONE_NAME = "VertiOne"


class SuperAdminCase(UsuarioCaseInterface):
    def obtener_firebase_usuario(self, params: CrearUsuarioFirebaseParams) -> FirebaseUser:
        usuario_actual: Usuario = params["usuario_actual"]
        usuario_nuevo: UsuarioCreate = params["usuario_nuevo"]
        compania: Compania = params["compania"]
        tipo_documento: TipoDocumento = params["tipo_documento"]
        
        if usuario_actual.rol not in [Rol.SUPER_ADMIN]:
            raise HTTPException(status_code=403, detail="No tienes permisos para crear usuarios")
            
        return mapear_usuario_dto_a_usuario_firebase(usuario_nuevo, compania, tipo_documento) 

    def obtener_usuario_a_guardar(self, params: CrearUsuarioParams) -> Usuario:
        usuario_actual: Usuario = params["usuario_actual"]
        usuario_nuevo: UsuarioCreate = params["usuario_nuevo"]

        if usuario_actual.rol not in [Rol.SUPER_ADMIN]:
            raise HTTPException(status_code=403, detail="No tienes permisos para crear usuarios")

        usuario = mapear_usuario_dto_a_usuario_create(usuario_nuevo, params["firebase_uid"])

        return usuario
        
    def obtener_filtros_para_listar_usuarios(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], rol: Optional[str]) -> dict:        
        filters = {
            "exact_filters": {},
            "ilike_filters": {},
            "like_filters": {}
        }
        
        if search:
            filters["ilike_filters"]["display_name"] = f"%{search}%"
        if company_id:
            filters["exact_filters"]["company_id"] = company_id
        if rol:
            filters["exact_filters"]["rol"] = rol
            
        return filters
    
    def obtener_filtro_para_totalizar_usuarios(self, usuario_actual: Usuario, company_id: Optional[UUID], rol: Optional[Rol]) -> dict:
        compania_id = company_id or usuario_actual.company_id
        filters = {
            "exact_filters": {
                "company_id": compania_id,
            },
            "ilike_filters": {},
            "like_filters": {}
        }

        if rol:
            filters["exact_filters"]["rol"] = rol

        return filters


    
