from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.models.clientes import Cliente
from app.db.models.compania import Compania
from app.db.models.enums.tipos_documento import TipoDocumento
from app.db.models.nivel_tecnico import NivelTecnico
from app.db.models.usuarios import Usuario
from app.schemas.web_superadmin import (
    WebSuperAdminCatalogItem,
)
from app.services.web.superadmin_users_service import WebSuperAdminUsersService


class WebSuperAdminService(WebSuperAdminUsersService):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_companies_catalog(self) -> list[WebSuperAdminCatalogItem]:
        result = await self.db.execute(select(Compania).order_by(Compania.nombre.asc()))
        companies = result.scalars().all()
        return [
            WebSuperAdminCatalogItem(id=str(company.id), name=company.nombre or "Sin nombre")
            for company in companies
        ]

    async def get_document_types_catalog(self) -> list[WebSuperAdminCatalogItem]:
        result = await self.db.execute(
            select(TipoDocumento).order_by(TipoDocumento.nombre.asc())
        )
        document_types = result.scalars().all()
        return [
            WebSuperAdminCatalogItem(id=str(document_type.id), name=document_type.nombre)
            for document_type in document_types
        ]

    async def get_technical_levels_catalog(
        self,
        company_id: UUID | None = None,
    ) -> list[WebSuperAdminCatalogItem]:
        query = select(NivelTecnico).order_by(NivelTecnico.nombre.asc())
        if company_id:
            query = query.where(NivelTecnico.compania_id == company_id)
        result = await self.db.execute(query)
        levels = result.scalars().all()
        return [
            WebSuperAdminCatalogItem(id=str(level.id), name=level.nombre)
            for level in levels
        ]

    async def get_company_clients_catalog(
        self,
        company_id: UUID,
    ) -> list[WebSuperAdminCatalogItem]:
        result = await self.db.execute(
            select(Cliente)
            .where(Cliente.compania_id == company_id)
            .order_by(Cliente.nombre.asc())
        )
        clients = result.scalars().all()
        return [
            WebSuperAdminCatalogItem(id=str(client.id), name=client.nombre or "Sin nombre")
            for client in clients
        ]
