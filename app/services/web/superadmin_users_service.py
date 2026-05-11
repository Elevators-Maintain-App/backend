from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.firebase import (
    FirebaseUser,
    FirebaseUserCreationError,
    actualizar_usuario_firestore,
    eliminar_usuario_firebase,
)
from app.db.models.compania import Compania
from app.db.models.enums.tipos_documento import TipoDocumento
from app.db.models.usuarios import Rol, Usuario
from app.db.repositories.usuarios import usuario_crud
from app.schemas.usuarios import UsuarioUpdate
from app.schemas.web.superadmin_users import (
    WebUserCreate,
    WebUserDeleteResponse,
    WebUserDetail,
    WebUserDisableResponse,
    WebUserListItem,
    WebUserListResponse,
    WebUserUpdate,
)
from app.services.usuario.usuarios import UsuarioService


class WebSuperAdminUsersService:
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

    def _parse_status(self, status_value: str | None) -> str | None:
        if not status_value:
            return None
        normalized = status_value.strip().lower()
        if normalized not in {"active", "inactive", "unknown"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Status invalido. Valores validos: active, inactive, unknown",
            )
        if normalized == "unknown":
            return None
        return normalized

    def _status_from_usuario(self, usuario: Usuario) -> str:
        if usuario.is_active is True:
            return "active"
        if usuario.is_active is False:
            return "inactive"
        return "unknown"

    def _to_list_item(
        self,
        usuario: Usuario,
        company_name: str | None,
    ) -> WebUserListItem:
        return WebUserListItem(
            uid=usuario.uid,
            display_name=usuario.display_name,
            email=usuario.email,
            phone=usuario.phone_number,
            role=usuario.rol.value,
            company_id=usuario.company_id,
            company_name=company_name,
            photo_url=usuario.photo_url,
            is_active=usuario.is_active,
            status=self._status_from_usuario(usuario),
            created_at=usuario.created_at,
            updated_at=usuario.updated_at,
        )

    def _to_detail(self, usuario: Usuario) -> WebUserDetail:
        return WebUserDetail(
            id=usuario.id,
            uid=usuario.uid,
            display_name=usuario.display_name,
            email=usuario.email,
            phone=usuario.phone_number,
            phone_number=usuario.phone_number,
            role=usuario.rol.value,
            company_id=usuario.company_id,
            company_name=usuario.company.nombre if usuario.company else None,
            status=self._status_from_usuario(usuario),
            created_at=usuario.created_at,
            updated_at=usuario.updated_at,
            photo_url=usuario.photo_url,
            is_active=usuario.is_active,
            document_id=usuario.document_id,
            document_type_id=usuario.document_type_id,
            document_type_name=usuario.document_type.nombre if usuario.document_type else None,
            client_id=usuario.client_id,
            nivel=usuario.nivel,
        )

    async def _get_usuario_or_404(self, uid: str) -> Usuario:
        usuario = await usuario_crud.get_usuario_con_relaciones(self.db, uid)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        return usuario

    async def _get_default_document_type_id(self) -> int:
        result = await self.db.execute(select(TipoDocumento.id).order_by(TipoDocumento.id.asc()))
        document_type_id = result.scalars().first()
        if not document_type_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay tipos de documento configurados para crear usuarios web",
            )
        return int(document_type_id)

    async def _validate_company_exists(self, company_id: UUID | None) -> UUID:
        if not company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="company_id es requerido para crear usuarios web",
            )
        company = await self.db.get(Compania, company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La compania no existe",
            )
        return company_id

    async def _sync_firestore_best_effort(self, usuario: Usuario) -> None:
        await actualizar_usuario_firestore(
            usuario.uid,
            {
                "uid": usuario.uid,
                "company_id": str(usuario.company_id) if usuario.company_id else None,
                "company_name": usuario.company.nombre if usuario.company else None,
                "display_name": usuario.display_name,
                "document_id": usuario.document_id,
                "document_type": str(usuario.document_type_id) if usuario.document_type_id else None,
                "document_type_name": usuario.document_type.nombre if usuario.document_type else None,
                "email": usuario.email,
                "photo_url": usuario.photo_url,
                "rol": usuario.rol.value,
                "client_id": str(usuario.client_id) if usuario.client_id else None,
                "client_name": usuario.client.nombre if usuario.client else None,
                "is_active": usuario.is_active,
            },
        )

    async def get_users_summary(self):
        from app.schemas.web_superadmin import WebSuperAdminUsersSummary

        total_users = await usuario_crud.count_web_superadmin_users(self.db)
        return WebSuperAdminUsersSummary(total_users=total_users)

    async def get_users(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        role: str | None = None,
        company_id: UUID | None = None,
        status_value: str | None = None,
    ) -> WebUserListResponse:
        rol = self._parse_role(role)
        normalized_status = self._parse_status(status_value)
        normalized_search = search.strip() if search and search.strip() else None
        skip = (page - 1) * page_size
        total = await usuario_crud.count_web_superadmin_users(
            self.db,
            search=normalized_search,
            rol=rol,
            company_id=company_id,
            status=normalized_status,
        )
        rows = await usuario_crud.list_web_superadmin_users(
            self.db,
            skip=skip,
            limit=page_size,
            search=normalized_search,
            rol=rol,
            company_id=company_id,
            status=normalized_status,
        )
        items = [self._to_list_item(usuario, company_name) for usuario, company_name in rows]
        return WebUserListResponse.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_user_detail(self, uid: str) -> WebUserDetail:
        usuario = await self._get_usuario_or_404(uid)
        return self._to_detail(usuario)

    async def create_user(
        self,
        *,
        current_user: FirebaseUser,
        payload: WebUserCreate,
        request_id: str | None = None,
    ) -> WebUserDetail:
        role_value = payload.role or payload.rol
        rol = self._parse_role(role_value)
        if rol is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="role es requerido",
            )

        company_id = await self._validate_company_exists(payload.company_id)
        email = str(payload.email).strip().lower()
        existing = await usuario_crud.get_by_field(self.db, "email", email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El email ya existe",
            )

        document_type_id = payload.document_type_id or await self._get_default_document_type_id()
        # TODO: pedir document_id/document_type_id en el contrato web definitivo.
        document_id = payload.document_id or email
        phone_number = payload.phone_number if payload.phone_number is not None else payload.phone

        usuario_data = {
            "company_id": company_id,
            "display_name": payload.display_name.strip(),
            "document_id": document_id,
            "document_type_id": document_type_id,
            "email": email,
            "phone_number": phone_number or "",
            "rol": rol,
            "client_id": payload.client_id,
            "nivel": payload.nivel,
            "is_active": payload.is_active if payload.is_active is not None else True,
        }

        try:
            created = await UsuarioService(self.db).create(
                current_user,
                usuario_data,
                photo=None,
                request_id=request_id,
            )
        except HTTPException as exc:
            if exc.status_code == status.HTTP_400_BAD_REQUEST and "existe" in str(exc.detail).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El email ya existe",
                ) from exc
            raise

        usuario = await self._get_usuario_or_404(created.uid)
        return self._to_detail(usuario)

    async def update_user(self, uid: str, payload: WebUserUpdate) -> WebUserDetail:
        usuario = await self._get_usuario_or_404(uid)
        update_data = payload.model_dump(exclude_unset=True)

        role_value = update_data.pop("role", None) or update_data.pop("rol", None)
        if role_value is not None:
            update_data["rol"] = self._parse_role(role_value)

        if "phone" in update_data:
            update_data["phone_number"] = update_data.pop("phone")

        status_value = update_data.pop("status", None)
        if status_value is not None:
            update_data["is_active"] = status_value == "active"

        for field in ("display_name", "company_id", "rol", "is_active"):
            if field in update_data and update_data[field] is None:
                update_data.pop(field)

        if update_data.get("company_id") is not None:
            await self._validate_company_exists(update_data["company_id"])

        if not update_data:
            return self._to_detail(usuario)

        await usuario_crud.update(self.db, db_obj=usuario, obj_in=UsuarioUpdate(**update_data))
        usuario_actualizado = await self._get_usuario_or_404(uid)
        await self._sync_firestore_best_effort(usuario_actualizado)
        return self._to_detail(usuario_actualizado)

    async def disable_user(
        self,
        *,
        uid: str,
        current_user: FirebaseUser,
    ) -> WebUserDisableResponse:
        if uid == current_user.uid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes inhabilitar tu propio usuario",
            )
        usuario = await self._get_usuario_or_404(uid)
        await usuario_crud.update(
            self.db,
            db_obj=usuario,
            obj_in={"is_active": False},
        )
        usuario_actualizado = await self._get_usuario_or_404(uid)
        # TODO: evaluar deshabilitar Firebase Auth con firebase_auth.update_user(disabled=True)
        # cuando exista politica de compatibilidad para mobile/web.
        await self._sync_firestore_best_effort(usuario_actualizado)
        return WebUserDisableResponse(
            uid=uid,
            status="inactive",
            message="Usuario inhabilitado",
        )

    async def delete_user(
        self,
        *,
        uid: str,
        current_user: FirebaseUser,
    ) -> WebUserDeleteResponse:
        if uid == current_user.uid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes eliminar tu propio usuario",
            )
        usuario = await self._get_usuario_or_404(uid)
        try:
            await eliminar_usuario_firebase(uid)
        except FirebaseUserCreationError as exc:
            if exc.error_code != "USER_NOT_FOUND":
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="No fue posible eliminar el usuario en Firebase",
                ) from exc

        await self.db.delete(usuario)
        await self.db.commit()
        return WebUserDeleteResponse(
            uid=uid,
            deleted=True,
            message="Usuario eliminado",
        )
