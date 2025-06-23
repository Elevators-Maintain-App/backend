from app.db.models.clientes import Cliente
from app.schemas.clientes import ClienteCreate, ClienteUpdate
from app.db.repositories.base import CRUDBaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional, List


class CRUDClientes(CRUDBaseRepository[Cliente, ClienteCreate, ClienteUpdate]):
    async def get_cliente_con_relaciones(self, db: AsyncSession, cliente_id: UUID) -> Cliente:
        result = await db.execute(
            select(Cliente).options(
                selectinload(Cliente.pais),
                selectinload(Cliente.tipos_documento),
            ).where(Cliente.id == cliente_id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi_with_advanced_filters_and_relations(self, db: AsyncSession, skip: Optional[int] = 0, limit: Optional[int] = None, exact_filters: Optional[dict] = None, ilike_filters: Optional[dict] = None, like_filters: Optional[dict] = None) -> List[Cliente]:
        query = select(Cliente).options(
            selectinload(Cliente.pais),
            selectinload(Cliente.tipos_documento),
        )
        return await self.get_multi_with_advanced_filters(db, skip, limit, exact_filters, ilike_filters, like_filters)

cliente_crud = CRUDClientes(Cliente)