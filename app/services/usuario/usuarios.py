# app/services/usuarios.py

from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, UploadFile
from sqlalchemy import select
import logging

from app.db.models.usuarios import Usuario
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate, UsuarioOut
from app.db.repositories.usuarios import usuario_crud
from app.services.compania import CompaniaService
from app.db.repositories.tipos_documento import tipo_documento_crud
from app.services.usuario.user_cases import FabricaDeUsuarios
from app.auth.firebase import (
    FirebaseUser,
    FirebaseUserCreationError,
    UsuarioFirebaseCreate,
    actualizar_usuario_firestore,
    crear_usuario_firebase,
    obtener_usuario_firebase_por_email,
)
from app.db.models.usuarios import Rol
from app.schemas.comunes import PaginacionResponse
from app.services.usuario.usuarios_mapper import usuario_to_usuario_out, usuarios_to_usuarios_out
from app.db.repositories.clientes import cliente_crud
from app.db.models.clientes import Cliente
from app.services.usuario.interfaces.usuario_case import CrearUsuarioParams, CrearUsuarioFirebaseParams
from app.services.firebase_storage.firebase_storage import subir_archivo_a_storage
from app.services.plans import PlanEnforcementService


logger = logging.getLogger(__name__)


class UsuarioService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_cliente_para_usuario_client(
        self,
        *,
        rol: Rol,
        client_id: Optional[UUID],
        company_id: UUID,
    ) -> Cliente | None:
        if rol != Rol.CLIENT:
            return None
        if not client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El client_id es requerido para usuarios client",
            )
        cliente = await cliente_crud.get_by_field(self.db, "id", client_id)
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El cliente no existe",
            )
        if cliente.compania_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El cliente no pertenece a la compania del usuario",
            )
        return cliente

    async def _sync_usuario_firestore(self, usuario: Usuario) -> None:
        cliente = usuario.client
        await actualizar_usuario_firestore(
            usuario.uid,
            {
                "uid": usuario.uid,
                "company_id": str(usuario.company_id) if usuario.company_id else None,
                "company_name": usuario.company.nombre if usuario.company else None,
                "display_name": usuario.display_name,
                "document_id": str(usuario.document_id) if usuario.document_id else None,
                "document_type": str(usuario.document_type_id) if usuario.document_type_id else None,
                "document_type_name": usuario.document_type.nombre if usuario.document_type else None,
                "email": usuario.email,
                "photo_url": usuario.photo_url,
                "rol": usuario.rol.value,
                "client_id": str(usuario.client_id) if usuario.client_id else None,
                "client_name": cliente.nombre if cliente else None,
                "is_active": usuario.is_active,
            },
        )

    async def _sync_firebase_user_firestore(
        self,
        uid: str,
        usuario_firebase: UsuarioFirebaseCreate,
    ) -> None:
        await actualizar_usuario_firestore(
            uid,
            {
                "uid": uid,
                "company_id": str(usuario_firebase.company_id) if usuario_firebase.company_id else None,
                "company_name": usuario_firebase.company_name,
                "display_name": usuario_firebase.display_name,
                "document_id": str(usuario_firebase.document_id) if usuario_firebase.document_id else None,
                "document_type": usuario_firebase.document_type,
                "document_type_name": usuario_firebase.document_type_name,
                "email": usuario_firebase.email,
                "photo_url": usuario_firebase.photo_url,
                "rol": usuario_firebase.rol.value,
                "client_id": str(usuario_firebase.client_id) if usuario_firebase.client_id else None,
                "client_name": usuario_firebase.client_name,
                "is_active": True,
            },
        )

    async def _crear_o_recuperar_usuario_firebase(
        self,
        usuario_firebase: UsuarioFirebaseCreate,
        *,
        request_id: str | None = None,
    ) -> tuple[FirebaseUser, bool]:
        try:
            return await crear_usuario_firebase(usuario_firebase), True
        except FirebaseUserCreationError as exc:
            if exc.error_code != "EMAIL_ALREADY_EXISTS":
                logger.exception(
                    "user_create_firebase_failed request_id=%s email=%s error_code=%s",
                    request_id,
                    usuario_firebase.email,
                    exc.error_code,
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="No fue posible crear el usuario en Firebase Auth",
                ) from exc

            try:
                firebase_user = await obtener_usuario_firebase_por_email(usuario_firebase)
            except FirebaseUserCreationError as lookup_exc:
                logger.exception(
                    "user_create_firebase_existing_lookup_failed request_id=%s email=%s error_code=%s",
                    request_id,
                    usuario_firebase.email,
                    lookup_exc.error_code,
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Firebase Auth reporto un email existente, pero no fue posible recuperar el usuario",
                ) from lookup_exc
            logger.warning(
                "user_create_recovering_existing_firebase_auth request_id=%s uid=%s email=%s",
                request_id,
                firebase_user.uid,
                usuario_firebase.email,
            )
            return firebase_user, False

    async def get_usuarios_con_paginacion(self, usuario_actual: Usuario, skip: Optional[int], limit: Optional[int] = None, search: Optional[str] = None, company_id: Optional[str] = None, rol: Optional[str] = None) -> PaginacionResponse[UsuarioOut]:
        try:
            fabrica_de_usuarios = FabricaDeUsuarios.get_user_case(usuario_actual.rol)
            filtros = fabrica_de_usuarios.obtener_filtros_para_listar_usuarios(usuario_actual, search, company_id, rol)
            users = await usuario_crud.get_usuarios_con_relaciones_con_paginacion(self.db, skip=skip, limit=limit, exact_filters=filtros.get("exact_filters", None), ilike_filters=filtros.get("ilike_filters", None), like_filters=filtros.get("like_filters", None))            
            usuarios_out = usuarios_to_usuarios_out(users)
            total_usuarios = await self._total_usuarios_con_filtro(filtros)
            return PaginacionResponse(
                data=usuarios_out,
                total=total_usuarios,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            print("**** get_all", e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener los usuarios")
        
    async def _total_usuarios_con_filtro(self, filtros: dict) -> int:
        cantidad_de_usuarios = await usuario_crud.get_total_with_advanced_filters(
            self.db, 
            exact_filters=filtros.get("exact_filters", None), 
            ilike_filters=filtros.get("ilike_filters", None), 
            like_filters=filtros.get("like_filters", None)
        )
        return cantidad_de_usuarios
        
    async def get_total_usuarios(self, usuario_actual: Usuario, company_id: Optional[UUID] = None, rol: Optional[Rol] = None) -> int:
        try:
            fabrica_de_usuarios = FabricaDeUsuarios.get_user_case(usuario_actual.rol)
            filtro_para_totalizar_usuarios = fabrica_de_usuarios.obtener_filtro_para_totalizar_usuarios(
                usuario_actual=usuario_actual, 
                company_id=company_id, 
                rol=rol
            )
            cantidad_de_usuarios = await usuario_crud.get_total_with_advanced_filters(
                self.db, 
                exact_filters=filtro_para_totalizar_usuarios.get("exact_filters", None), 
                ilike_filters=filtro_para_totalizar_usuarios.get("ilike_filters", None), 
                like_filters=filtro_para_totalizar_usuarios.get("like_filters", None)
            )
            return cantidad_de_usuarios
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener la cantidad de usuarios")

    async def get_by_uid(self, uid: str) -> UsuarioOut:
        usuario = await usuario_crud.get_usuario_con_relaciones(self.db, uid)
        if not usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        usuario_out = usuario_to_usuario_out(usuario)
        return usuario_out

    async def create(
        self,
        usuario_actual: Usuario,
        usuario_data: Dict[str, Any],
        photo: Optional[UploadFile] = None,
        request_id: str | None = None,
    ) -> UsuarioOut:
        # Validar y normalizar company_id según las reglas del rol del usuario actual
        fabrica_de_usuarios = FabricaDeUsuarios.get_user_case(usuario_actual.rol)
        company_id_proporcionado = usuario_data.get("company_id")
        company_id_normalizado = fabrica_de_usuarios.validar_y_normalizar_company_id(
            usuario_actual, 
            company_id_proporcionado
        )
        usuario_data["company_id"] = company_id_normalizado
        if usuario_data.get("email"):
            usuario_data["email"] = str(usuario_data["email"]).strip().lower()
        
        # Convert dict to UsuarioCreate for validation and use in existing logic
        usuario_in = UsuarioCreate(**usuario_data)
        
        usuario_existente = await usuario_crud.get_by_field(self.db, "email", usuario_in.email)
        if usuario_existente:
            usuario_con_relaciones = await usuario_crud.get_usuario_con_relaciones(
                self.db,
                usuario_existente.uid,
            )
            try:
                await self._sync_usuario_firestore(usuario_con_relaciones or usuario_existente)
                logger.warning(
                    "user_create_duplicate_postgres_synced_firestore request_id=%s uid=%s email=%s",
                    request_id,
                    usuario_existente.uid,
                    usuario_in.email,
                )
            except Exception:
                logger.exception(
                    "user_create_duplicate_postgres_firestore_sync_failed request_id=%s uid=%s email=%s",
                    request_id,
                    usuario_existente.uid,
                    usuario_in.email,
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario ya existe en VertiOne",
            )

        compania = await CompaniaService(self.db).get_compania(usuario_in.company_id, usuario_actual)
        cliente = await self._get_cliente_para_usuario_client(
            rol=usuario_in.rol,
            client_id=usuario_in.client_id,
            company_id=usuario_in.company_id,
        )
        tipo_documento = await tipo_documento_crud.get(self.db, usuario_in.document_type_id)

        plan_enforcement = PlanEnforcementService(self.db)
        await plan_enforcement.assert_can_create_user(usuario_in.company_id, usuario_in.rol)

        if photo and photo.filename:
            try:
                contenido_foto = await photo.read()
                content_type = photo.content_type or "image/jpeg"

                photo_url = subir_archivo_a_storage(
                    archivo_bytes=contenido_foto,
                    compania_id=usuario_in.company_id,
                    entidad="users",
                    entidad_id=uuid4(),
                    nombre_archivo="photo",
                    tipo_archivo="photo",
                    content_type=content_type
                )

                usuario_data["photo_url"] = photo_url
                usuario_in = UsuarioCreate(**usuario_data)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error al subir la foto: {str(e)}"
                )

        usuario_firebase = fabrica_de_usuarios.obtener_firebase_usuario(CrearUsuarioFirebaseParams(
            usuario_actual=usuario_actual,
            usuario_nuevo=usuario_in,
            compania=compania,
            tipo_documento=tipo_documento,
            cliente=cliente
        ))

        usuario_firebase, firebase_user_created = await self._crear_o_recuperar_usuario_firebase(
            usuario_firebase,
            request_id=request_id,
        )

        usuario_existente_por_uid = await usuario_crud.get_usuario_con_relaciones(
            self.db,
            usuario_firebase.uid,
        )
        if usuario_existente_por_uid:
            try:
                await self._sync_usuario_firestore(usuario_existente_por_uid)
            except Exception:
                logger.exception(
                    "user_create_existing_uid_firestore_sync_failed request_id=%s uid=%s email=%s",
                    request_id,
                    usuario_firebase.uid,
                    usuario_in.email,
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario ya existe en VertiOne",
            )

        usuario_a_guardar: Usuario = None
        usuario_a_guardar = fabrica_de_usuarios.obtener_usuario_a_guardar(CrearUsuarioParams(
            usuario_actual=usuario_actual,
            usuario_nuevo=usuario_in,
            firebase_uid=usuario_firebase.uid
        ))
        try:
            usuario_guardado = await usuario_crud.create(self.db, obj_in=usuario_a_guardar)
        except Exception as exc:
            logger.exception(
                "user_create_postgres_failed request_id=%s uid=%s email=%s",
                request_id,
                usuario_firebase.uid,
                usuario_in.email,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Firebase Auth fue creado o recuperado, pero no fue posible crear el usuario en VertiOne",
            ) from exc

        try:
            await plan_enforcement.refresh_current_usage_snapshot(usuario_guardado.company_id)
        except Exception:
            logger.exception(
                "user_create_usage_snapshot_refresh_failed request_id=%s uid=%s email=%s",
                request_id,
                usuario_firebase.uid,
                usuario_in.email,
            )

        usuario_guardado = await usuario_crud.get_usuario_con_relaciones(
            self.db,
            usuario_firebase.uid,
        ) or usuario_guardado

        try:
            await self._sync_usuario_firestore(usuario_guardado)
        except Exception:
            logger.exception(
                "user_create_firestore_sync_failed_non_blocking request_id=%s uid=%s email=%s",
                request_id,
                usuario_firebase.uid,
                usuario_in.email,
            )

        try:
            if firebase_user_created and usuario_firebase.password:
                await fabrica_de_usuarios.enviar_email_de_bienvenida(
                    usuario_a_guardar.email,
                    usuario_a_guardar.display_name,
                    usuario_firebase.password,
                )
            else:
                logger.info(
                    "user_create_recovered_partial_user request_id=%s uid=%s email=%s",
                    request_id,
                    usuario_firebase.uid,
                    usuario_in.email,
                )
        except Exception:
            logger.exception(
                "user_create_welcome_email_failed_non_blocking request_id=%s uid=%s email=%s",
                request_id,
                usuario_firebase.uid,
                usuario_in.email,
            )

        return usuario_to_usuario_out(usuario_guardado)
        
        

    async def update(self, uid: str, usuario_in: UsuarioUpdate) -> UsuarioOut:
        usuario = await usuario_crud.get_usuario_con_relaciones(self.db, uid)
        if not usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

        update_data = usuario_in.model_dump(exclude_unset=True)
        target_rol = update_data.get("rol", usuario.rol)
        target_company_id = update_data.get("company_id", usuario.company_id)
        target_client_id = update_data.get("client_id", usuario.client_id)
        await self._get_cliente_para_usuario_client(
            rol=target_rol,
            client_id=target_client_id,
            company_id=target_company_id,
        )

        await usuario_crud.update(self.db, db_obj=usuario, obj_in=usuario_in)
        usuario_actualizado = await usuario_crud.get_usuario_con_relaciones(self.db, uid)
        await self._sync_usuario_firestore(usuario_actualizado)
        return usuario_to_usuario_out(usuario_actualizado)

    async def delete(self, uid: str) -> None:
        usuario = await self.get_by_uid(uid)
        return await usuario_crud.remove(self.db, db_obj=usuario)
