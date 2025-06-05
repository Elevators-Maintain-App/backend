from abc import ABC
from app.auth.firebase import FirebaseUser
from app.db.models.usuarios import Usuario
from app.schemas.usuarios import UsuarioCreate


class UsuarioCaseInterface(ABC):
    def obtener_firebase_usuario(self, usuario_nuevo: UsuarioCreate) -> FirebaseUser:
        pass

    def obtener_usuario_a_guardar(self, usuario_nuevo: UsuarioCreate) -> Usuario:
        pass