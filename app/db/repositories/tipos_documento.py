from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.models.enums.tipos_documento import TipoDocumento
from app.schemas.tipos_documento import TipoDocumentoCreate, TipoDocumentoUpdate
from app.db.repositories.base import CRUDBaseRepository

class CRUDTiposDocumento(CRUDBaseRepository[TipoDocumento, TipoDocumentoCreate, TipoDocumentoUpdate]):
    
    async def get_available_for_company(
        self, 
        db: AsyncSession, 
        company_id: str
    ) -> List[TipoDocumento]:
        """
        Get document types available for a company (system-wide + owned by company)
        """
        query = select(TipoDocumento).where(
            (TipoDocumento.is_system_wide == True) |  # System types
            (TipoDocumento.owner_compania_id == company_id)  # Company's own types
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_owned_by_company(
        self, 
        db: AsyncSession, 
        company_id: str
    ) -> List[TipoDocumento]:
        """
        Get document types owned/created by a specific company
        """
        query = select(TipoDocumento).where(
            TipoDocumento.owner_compania_id == company_id
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_system_types(self, db: AsyncSession) -> List[TipoDocumento]:
        """
        Get all system-wide document types
        """
        query = select(TipoDocumento).where(
            TipoDocumento.is_system_wide == True
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_with_relationships(
        self, 
        db: AsyncSession, 
        id: int
    ) -> Optional[TipoDocumento]:
        """
        Get document type with owner and companies using it
        """
        query = (
            select(TipoDocumento)
            .where(TipoDocumento.id == id)
            .options(
                selectinload(TipoDocumento.owner_compania),
                selectinload(TipoDocumento.companies_using_this_type)
            )
        )
        result = await db.execute(query)
        return result.scalars().first()

tipo_documento_crud = CRUDTiposDocumento(TipoDocumento)