from abc import ABC
from app.auth.firebase import FirebaseUser
from app.schemas.usuarios import UsuarioCreate


class UsuarioCaseInterface(ABC):
    def obtener_firebase_usuario(self, usuario_nuevo: UsuarioCreate) -> FirebaseUser:
        ...

    def obtener_usuario_a_guardar(self, usuario_nuevo: UsuarioCreate) -> UsuarioCreate:
        ...