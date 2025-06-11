# app/db/repositories/usuarios.py

from app.db.models.usuarios import Usuario
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDUsuarios(CRUDBaseRepository[Usuario, UsuarioCreate, UsuarioUpdate]):
    ...

usuario_crud = CRUDUsuarios(Usuario)
