# app/services/usuarios.py

from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, UploadFile
from sqlalchemy import select

from app.db.models.usuarios import Usuario
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate, UsuarioOut
from app.db.repositories.usuarios import usuario_crud
from app.services.compania import CompaniaService
from app.db.repositories.tipos_documento import tipo_documento_crud
from app.services.usuario.user_cases import FabricaDeUsuarios
from app.auth.firebase import actualizar_usuario_firestore, crear_usuario_firebase
from app.db.models.usuarios import Rol
from app.schemas.comunes import PaginacionResponse
from app.services.usuario.usuarios_mapper import usuario_to_usuario_out, usuarios_to_usuarios_out
from app.db.repositories.clientes import cliente_crud
from app.db.models.clientes import Cliente
from app.services.usuario.interfaces.usuario_case import CrearUsuarioParams, CrearUsuarioFirebaseParams
from app.services.firebase_storage.firebase_storage import subir_archivo_a_storage


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

    async def create(self, usuario_actual: Usuario, usuario_data: Dict[str, Any], photo: Optional[UploadFile] = None) -> UsuarioOut:
        # Upload photo first if provided, before creating Firebase user
        if photo and photo.filename:
            try:
                contenido_foto = await photo.read()
                content_type = photo.content_type or "image/jpeg"
                
                # Generate a UUID for the photo path (user_id doesn't exist yet)
                photo_user_id = uuid4()
                company_id = usuario_data.get("company_id")
                
                photo_url = subir_archivo_a_storage(
                    archivo_bytes=contenido_foto,
                    compania_id=company_id,
                    entidad="users",
                    entidad_id=photo_user_id,
                    nombre_archivo="photo",
                    tipo_archivo="photo",
                    content_type=content_type
                )
                
                usuario_data["photo_url"] = photo_url
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error al subir la foto: {str(e)}"
                )
        
        # Validar y normalizar company_id según las reglas del rol del usuario actual
        fabrica_de_usuarios = FabricaDeUsuarios.get_user_case(usuario_actual.rol)
        company_id_proporcionado = usuario_data.get("company_id")
        company_id_normalizado = fabrica_de_usuarios.validar_y_normalizar_company_id(
            usuario_actual, 
            company_id_proporcionado
        )
        usuario_data["company_id"] = company_id_normalizado
        
        # Convert dict to UsuarioCreate for validation and use in existing logic
        usuario_in = UsuarioCreate(**usuario_data)
        
        usuario = await usuario_crud.get_by_field(self.db, "email", usuario_in.email)
        if usuario:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario ya existe")

        compania = await CompaniaService(self.db).get_compania(usuario_in.company_id, usuario_actual)
        cliente = await self._get_cliente_para_usuario_client(
            rol=usuario_in.rol,
            client_id=usuario_in.client_id,
            company_id=usuario_in.company_id,
        )
        tipo_documento = await tipo_documento_crud.get(self.db, usuario_in.document_type_id)
        usuario_firebase = fabrica_de_usuarios.obtener_firebase_usuario(CrearUsuarioFirebaseParams(
            usuario_actual=usuario_actual,
            usuario_nuevo=usuario_in,
            compania=compania,
            tipo_documento=tipo_documento,
            cliente=cliente
        ))

        # crear usuario en firebase
        usuario_firebase = await crear_usuario_firebase(usuario_firebase)        
        usuario_a_guardar: Usuario = None
        usuario_a_guardar = fabrica_de_usuarios.obtener_usuario_a_guardar(CrearUsuarioParams(
            usuario_actual=usuario_actual,
            usuario_nuevo=usuario_in,
            firebase_uid=usuario_firebase.uid
        ))
        usuario_guardado = await usuario_crud.create(self.db, obj_in=usuario_a_guardar)

        await fabrica_de_usuarios.enviar_email_de_bienvenida(usuario_a_guardar.email, usuario_a_guardar.display_name, usuario_firebase.password)

        return usuario_guardado
        
        

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
