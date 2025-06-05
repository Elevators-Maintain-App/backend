from fastapi import HTTPException
import uuid
from app.db.models.compania import Compania
from app.db.models import TipoDocumento
from app.db.models.usuarios import Usuario
from app.schemas.usuarios import UsuarioCreate
from app.auth.firebase import UsuarioFirebaseDto
from pydantic import BaseModel
from .utils import mapear_usuario_dto_a_usuario_firebase, mapear_usuario_dto_a_usuario
from app.services.usuario.interfaces import UsuarioCaseInterface


VERTIONE_COMPANY_ID = "00000000-0000-0000-0000-000000000000"
VERTIONE_NAME = "VertiOne"

class CrearUsuarioParams(BaseModel):
    usuario_actual: Usuario
    usuario_nuevo: UsuarioCreate
    compania: Compania
    tipo_documento: TipoDocumento   


class AdminCase(UsuarioCaseInterface):
    def obtener_firebase_usuario(self, params: CrearUsuarioParams) -> UsuarioFirebaseDto:
        usuario_actual: Usuario = params.usuario_actual
        usuario_nuevo: UsuarioCreate = params.usuario_nuevo
        compania: Compania = params.compania
        tipo_documento: TipoDocumento = params.tipo_documento
        
        if usuario_actual.rol not in ["admin"]:
            raise HTTPException(status_code=403, detail="No tienes permisos para crear usuarios")
        
        return mapear_usuario_dto_a_usuario_firebase(usuario_nuevo, compania, tipo_documento)
    
    def obtener_usuario_a_guardar(self, params: CrearUsuarioParams) -> Usuario:
        usuario_actual: Usuario = params.usuario_actual
        usuario_nuevo: UsuarioCreate = params.usuario_nuevo
        
        if usuario_actual.rol not in ["admin"]:
            raise HTTPException(status_code=403, detail="No tienes permisos para crear usuarios")
        
        usuario = mapear_usuario_dto_a_usuario(usuario_nuevo, params.firebase_uid)
        usuario.company_id = usuario_actual.company_id
        
        return usuario
    
