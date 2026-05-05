# app/db/repositories/usuarios.py

from app.db.models.usuarios import Usuario
from app.db.models.compania import Compania
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate
from app.db.repositories.base import CRUDBaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import func, or_, select
from typing import List

class CRUDUsuarios(CRUDBaseRepository[Usuario, UsuarioCreate, UsuarioUpdate]):
    async def get_usuario_con_relaciones(self, db: AsyncSession, uid: str) -> Usuario:
        query = select(Usuario).where(Usuario.uid == uid).options(
            joinedload(Usuario.company),
            joinedload(Usuario.document_type),
            joinedload(Usuario.client),
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

    def _web_superadmin_filters(self, search: str | None = None, rol=None) -> list:
        filters = []
        if rol is not None:
            filters.append(Usuario.rol == rol)
        if search:
            search_pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Usuario.email.ilike(search_pattern),
                    Usuario.display_name.ilike(search_pattern),
                    Usuario.document_id.ilike(search_pattern),
                )
            )
        return filters

    async def count_web_superadmin_users(
        self,
        db: AsyncSession,
        search: str | None = None,
        rol=None,
    ) -> int:
        filters = self._web_superadmin_filters(search=search, rol=rol)
        query = select(func.count()).select_from(Usuario).where(*filters)
        result = await db.execute(query)
        return result.scalar() or 0

    async def list_web_superadmin_users(
        self,
        db: AsyncSession,
        skip: int,
        limit: int,
        search: str | None = None,
        rol=None,
    ) -> list[tuple[Usuario, str | None]]:
        filters = self._web_superadmin_filters(search=search, rol=rol)
        query = (
            select(Usuario, Compania.nombre.label("company_name"))
            .outerjoin(Compania, Usuario.company_id == Compania.id)
            .where(*filters)
            .order_by(Usuario.created_at.desc(), Usuario.uid.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return [(row[0], row[1]) for row in result.all()]

usuario_crud = CRUDUsuarios(Usuario)
