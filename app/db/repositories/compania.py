from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.repositories.base import BaseRepository, CRUDBaseRepository
from app.db.models.compania import Compania
from app.schemas.compania import CompaniaCreate, CompaniaUpdate

class CompaniaRepository(BaseRepository[Compania, CompaniaCreate, CompaniaUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Compania, db=db)
    
    async def get_by_documento(self, documento: str) -> Optional[Compania]:
        """
        Obtiene una compañía por su documento
        """
        return await self.get_by_field("documento", documento)
    
    async def get_by_tipo_documento(self, tipo_documento_id: int, skip: int = 0, limit: int = 100) -> List[Compania]:
        """
        Obtiene todas las compañías por tipo de documento
        """
        query = (
            select(self.model)
            .where(self.model.tipo_documento_id == tipo_documento_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all() 
    
    async def get_with_relations(self, compania_id: str) -> Optional[Compania]:
        """
        Obtiene una compañía con sus relaciones principales
        """
        query = (
            select(self.model)
            .where(self.model.id == compania_id)
            .options(
                selectinload(self.model.document_type),
                selectinload(self.model.pais),
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def get_with_basic_relations(self, compania_id: str) -> Optional[Compania]:
        """
        Obtiene una compañía con sus relaciones básicas (más ligero)
        """
        query = (
            select(self.model)
            .where(self.model.id == compania_id)
            .options(
                selectinload(self.model.document_type),
                selectinload(self.model.pais)
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()

# Create CRUD instance for advanced filtering methods
class CRUDCompania(CRUDBaseRepository[Compania, CompaniaCreate, CompaniaUpdate]):
    async def get_multi_with_relations(self, db: AsyncSession, *, skip: int = 0, limit: int = 100, **kwargs) -> List[Compania]:
        """
        Get multiple companies with their relationships loaded
        """
        query = (
            select(self.model)
            .options(
                selectinload(self.model.document_type),
                selectinload(self.model.pais),
            )
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_multi_with_advanced_filters_and_relations(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        exact_filters: dict = None,
        ilike_filters: dict = None,
        like_filters: dict = None
    ) -> List[Compania]:
        """
        Get multiple companies with advanced filters and relationships loaded
        """
        query = select(self.model).options(
            selectinload(self.model.document_type),
            selectinload(self.model.pais),
        )
        
        # Apply filters
        if exact_filters:
            for field, value in exact_filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        if ilike_filters:
            for field, value in ilike_filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field).ilike(value))
        
        if like_filters:
            for field, value in like_filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field).like(value))
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

compania_crud = CRUDCompania(Compania)