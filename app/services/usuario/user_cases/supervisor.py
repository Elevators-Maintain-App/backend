from dataclasses import dataclass
from fastapi import HTTPException
from app.services.usuario.interfaces import UsuarioCaseInterface, CrearUsuarioFirebaseParams, CrearUsuarioParams
from app.db.models.compania import Compania
from app.db.models.usuarios import Usuario, Rol
from app.schemas.usuarios import UsuarioCreate
from app.auth.firebase import FirebaseUser
from app.db.models import TipoDocumento
from app.services.usuario.user_cases.utils import mapear_usuario_dto_a_usuario_firebase, mapear_usuario_dto_a_usuario_create
from typing import Optional

class SupervisorCase(UsuarioCaseInterface):
    def obtener_firebase_usuario(self, params: CrearUsuarioFirebaseParams) -> FirebaseUser:
        usuario_actual: Usuario = params["usuario_actual"]
        usuario_nuevo: UsuarioCreate = params["usuario_nuevo"]
        compania: Compania = params["compania"]
        tipo_documento: TipoDocumento = params["tipo_documento"]
        
        if usuario_actual.rol not in [Rol.SUPERVISOR]:
            raise HTTPException(status_code=403, detail="No tienes permisos para crear usuarios")

        if usuario_nuevo.rol not in [Rol.TECHNICIAN]:
            raise HTTPException(status_code=403, detail="No tienes permisos para crear usuarios")
        
        return mapear_usuario_dto_a_usuario_firebase(usuario_nuevo, compania, tipo_documento)
    
    def obtener_usuario_a_guardar(self, params: CrearUsuarioParams) -> Usuario:
        usuario_actual: Usuario = params["usuario_actual"]
        usuario_nuevo: UsuarioCreate = params["usuario_nuevo"]
        
        if usuario_actual.rol not in [Rol.SUPERVISOR]:
            raise HTTPException(status_code=403, detail="No tienes permisos para crear usuarios")
        
        if usuario_nuevo.rol not in [Rol.TECHNICIAN]:
            raise HTTPException(status_code=403, detail="No tienes permisos para crear usuarios")
        
        usuario = mapear_usuario_dto_a_usuario_create(usuario_nuevo, params["firebase_uid"])
        usuario.company_id = usuario_actual.company_id

        return usuario
    
    def obtener_filtros(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], rol: Optional[str]) -> dict:
        result = {
            "exact_filters": {
                "company_id": usuario_actual.company_id,
                "rol": Rol.TECHNICIAN.value
            },
            "ilike_filters": {}
        }
        if search:
            result["ilike_filters"]["display_name"] = f"%{search}%"

        return result   