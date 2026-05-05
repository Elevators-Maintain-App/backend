from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.usuarios import Rol, Usuario
from app.db.repositories.usuarios import usuario_crud
from app.schemas.web_superadmin import (
    WebSuperAdminUserItem,
    WebSuperAdminUsersPage,
    WebSuperAdminUsersSummary,
)


class WebSuperAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _parse_role(self, role: str | None) -> Rol | None:
        if not role:
            return None
        try:
            return Rol(role)
        except ValueError:
            valid_roles = ", ".join(rol.value for rol in Rol)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Rol invalido: {role}. Roles validos: {valid_roles}",
            )

    def _to_item(
        self,
        usuario: Usuario,
        company_name: str | None,
    ) -> WebSuperAdminUserItem:
        return WebSuperAdminUserItem(
            uid=usuario.uid,
            email=usuario.email,
            display_name=usuario.display_name,
            role=usuario.rol.value,
            company_id=usuario.company_id,
            company_name=company_name,
            photo_url=usuario.photo_url,
            is_active=bool(usuario.is_active),
        )

    async def get_users_summary(self) -> WebSuperAdminUsersSummary:
        total_users = await usuario_crud.count_web_superadmin_users(self.db)
        return WebSuperAdminUsersSummary(total_users=total_users)

    async def get_users(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        role: str | None = None,
    ) -> WebSuperAdminUsersPage:
        rol = self._parse_role(role)
        normalized_search = search.strip() if search and search.strip() else None
        skip = (page - 1) * page_size
        total = await usuario_crud.count_web_superadmin_users(
            self.db,
            search=normalized_search,
            rol=rol,
        )
        rows = await usuario_crud.list_web_superadmin_users(
            self.db,
            skip=skip,
            limit=page_size,
            search=normalized_search,
            rol=rol,
        )
        data = [self._to_item(usuario, company_name) for usuario, company_name in rows]
        return WebSuperAdminUsersPage.create(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
        )
