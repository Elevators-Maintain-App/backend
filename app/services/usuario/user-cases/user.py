from app.db.models.usuarios import Usuario
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate

class UserCase:
    def crear_usuario(self, usuario_actual: Usuario, usuario_nuevo: UsuarioCreate):
        ...