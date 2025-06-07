from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.repositories.base import BaseRepository
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
        Obtiene una compañía con sus relaciones
        """
        query = (
            select(self.model)
            .where(self.model.id == compania_id)
            .options(
                selectinload(self.model.document_type_in_use)
            )        )
        result = await self.db.execute(query)
        return result.scalars().first()