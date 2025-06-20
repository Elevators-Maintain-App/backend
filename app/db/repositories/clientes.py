from app.db.models.clientes import Cliente
from app.schemas.clientes import ClienteCreate, ClienteUpdate
from app.db.repositories.base import CRUDBaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID

class CRUDClientes(CRUDBaseRepository[Cliente, ClienteCreate, ClienteUpdate]):
    async def get_cliente_con_relaciones(self, db: AsyncSession, cliente_id: UUID) -> Cliente:
        result = await db.execute(
            select(Cliente).options(
                selectinload(Cliente.pais),
                selectinload(Cliente.tipos_documento),
            ).where(Cliente.id == cliente_id)
        )
        return result.scalar_one_or_none()

cliente_crud = CRUDClientes(Cliente)