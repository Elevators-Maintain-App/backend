# app/db/repositories/usuarios.py

from app.db.models.usuarios import Usuario
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate
from app.db.repositories.base import CRUDBaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select
# Line removed as the import is unused.

class CRUDUsuarios(CRUDBaseRepository[Usuario, UsuarioCreate, UsuarioUpdate]):
    async def get_usuario_con_relaciones(self, db: AsyncSession, uid: str) -> Usuario:
        query = select(Usuario).where(Usuario.uid == uid).options(
            joinedload(Usuario.company),
            joinedload(Usuario.document_type)
        )
        result = await db.execute(query)        
        return result.scalar_one_or_none()

usuario_crud = CRUDUsuarios(Usuario)
