from app.db.models.proyectos import Proyecto
from app.db.models.clientes import Cliente
from app.db.models.compania import Compania
from app.schemas.proyectos import ProyectoCreate, ProyectoUpdate
from app.db.repositories.base import CRUDBaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

class CRUDProyectos(CRUDBaseRepository[Proyecto, ProyectoCreate, ProyectoUpdate]):
    async def get_multi_with_advanced_filters(self, db: AsyncSession, skip: int = 0, limit: int = 100, exact_filters: dict = None, ilike_filters: dict = None, like_filters: dict = None) -> List[Proyecto]:
        query = select(self.model).options(
            selectinload(self.model.cliente),
            selectinload(self.model.compania)
        ).offset(skip).limit(limit)
        
        if exact_filters:
            for field, value in exact_filters.items():
                query = query.where(getattr(self.model, field) == value)
        if ilike_filters:
            for field, value in ilike_filters.items():
                query = query.where(getattr(self.model, field).ilike(value))
        if like_filters:
            for field, value in like_filters.items():
                query = query.where(getattr(self.model, field).like(value))
        result = await db.execute(query)
        
        return result.scalars().all()
    
    async def get_with_relationships(self, db: AsyncSession, id: any) -> Optional[Proyecto]:
        """Obtiene un proyecto con sus relaciones de cliente y compañía cargadas"""
        query = select(self.model).options(
            selectinload(self.model.cliente),
            selectinload(self.model.compania)
        ).where(self.model.id == id)
        
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_multi_with_relationships(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Proyecto]:
        """Obtiene múltiples proyectos con sus relaciones de cliente y compañía cargadas"""
        query = select(self.model).options(
            selectinload(self.model.cliente),
            selectinload(self.model.compania)
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

proyecto_crud = CRUDProyectos(Proyecto)