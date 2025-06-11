from abc import ABC
from app.auth.firebase import FirebaseUser
from app.schemas.usuarios import UsuarioCreate
from app.db.models.usuarios import Usuario
from app.db.models import Compania, TipoDocumento
from dataclasses import dataclass

@dataclass
class CrearUsuarioParams:
    usuario_actual: Usuario
    usuario_nuevo: UsuarioCreate
    firebase_uid: str

@dataclass
class CrearUsuarioFirebaseParams:
    usuario_actual: Usuario
    usuario_nuevo: UsuarioCreate
    compania: Compania
    tipo_documento: TipoDocumento
    firebase_uid: str

class UsuarioCaseInterface(ABC):
    def obtener_firebase_usuario(self, usuario_nuevo: UsuarioCreate) -> FirebaseUser:
        ...

    def obtener_usuario_a_guardar(self, usuario_nuevo: UsuarioCreate) -> UsuarioCreate:
        ...

    def obtener_filtros(self, usuario_actual: Usuario) -> dict:
        ...

