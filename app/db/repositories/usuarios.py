# app/db/repositories/usuarios.py

from app.db.models.usuarios import Usuario
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate
from app.db.repositories.base import CRUDBaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from typing import List

class CRUDUsuarios(CRUDBaseRepository[Usuario, UsuarioCreate, UsuarioUpdate]):
    async def get_usuario_con_relaciones(self, db: AsyncSession, uid: str) -> Usuario:
        query = select(Usuario).where(Usuario.uid == uid).options(
            joinedload(Usuario.company),
            joinedload(Usuario.document_type)
        )
        result = await db.execute(query)        
        return result.scalar_one_or_none()
    
    async def get_usuarios_con_relaciones_con_paginacion(self, db: AsyncSession, skip: int = 0, limit: int = 100, exact_filters: dict = None, ilike_filters: dict = None, like_filters: dict = None) -> List[Usuario]:
        query = select(Usuario).offset(skip).limit(limit).options(
            joinedload(Usuario.company),
            joinedload(Usuario.document_type)
        )
        if exact_filters:
            for field, value in exact_filters.items():
                query = query.where(getattr(Usuario, field) == value)
        if ilike_filters:
            for field, value in ilike_filters.items():
                query = query.where(getattr(Usuario, field).ilike(value))
        if like_filters:
            for field, value in like_filters.items():
                query = query.where(getattr(Usuario, field).like(value))
        result = await db.execute(query)        
        return result.scalars().all()

usuario_crud = CRUDUsuarios(Usuario)
