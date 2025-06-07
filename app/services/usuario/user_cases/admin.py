from fastapi import HTTPException
import uuid
from dataclasses import dataclass
from app.db.models.compania import Compania
from app.db.models import TipoDocumento
from app.db.models.usuarios import Usuario
from app.schemas.usuarios import UsuarioCreate
from app.auth.firebase import FirebaseUser
from .utils import mapear_usuario_dto_a_usuario_firebase, mapear_usuario_dto_a_usuario_create
from app.services.usuario.interfaces import UsuarioCaseInterface
from app.db.models.usuarios import Rol

VERTIONE_COMPANY_ID = "00000000-0000-0000-0000-000000000000"
VERTIONE_NAME = "VertiOne"

@dataclass
class CrearUsuarioFirebaseParams:
    usuario_actual: Usuario
    usuario_nuevo: UsuarioCreate
    compania: Compania
    tipo_documento: TipoDocumento
    firebase_uid: str

@dataclass
class CrearUsuarioParams:
    usuario_actual: Usuario
    usuario_nuevo: UsuarioCreate
    firebase_uid: str


class AdminCase(UsuarioCaseInterface):
    def obtener_firebase_usuario(self, params: CrearUsuarioFirebaseParams) -> FirebaseUser:
        usuario_actual: Usuario = params["usuario_actual"]
        usuario_nuevo: UsuarioCreate = params["usuario_nuevo"]
        compania: Compania = params["compania"]
        tipo_documento: TipoDocumento = params["tipo_documento"]
        
        if usuario_actual.rol not in [Rol.ADMIN, Rol.SUPER_ADMIN]:
            raise HTTPException(status_code=403, detail="No tienes permisos para crear usuarios")
        
        return mapear_usuario_dto_a_usuario_firebase(usuario_nuevo, compania, tipo_documento)
    
    def obtener_usuario_a_guardar(self, params: CrearUsuarioParams) -> UsuarioCreate:
        try:
            usuario_actual: Usuario = params["usuario_actual"]
            usuario_nuevo: UsuarioCreate = params["usuario_nuevo"]
            
            if usuario_actual.rol not in [Rol.ADMIN, Rol.SUPER_ADMIN]:
                raise HTTPException(status_code=403, detail="No tienes permisos para crear usuarios")        
            
            usuario = mapear_usuario_dto_a_usuario_create(usuario_nuevo, params["firebase_uid"])        
            usuario.company_id = usuario_actual.company_id
            
            return usuario
        except Exception as e:
            print("**** error", e)
            raise HTTPException(status_code=500, detail=str(e))
    
