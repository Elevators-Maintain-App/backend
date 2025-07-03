# app/services/usuarios.py

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy import select

from app.db.models.usuarios import Usuario
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate, UsuarioOut
from app.db.repositories.usuarios import usuario_crud
from app.services.compania import CompaniaService
from app.db.repositories.tipos_documento import tipo_documento_crud
from app.services.usuario.user_cases import FabricaDeUsuarios
from app.auth.firebase import crear_usuario_firebase
from app.db.models.usuarios import Rol
from app.schemas.comunes import PaginacionResponse
from app.services.usuario.usuarios_mapper import usuario_to_usuario_out, usuarios_to_usuarios_out
from app.services.notificaciones import NotificacionService, TipoNotificacion
from app.services.notificaciones.templates import TemplateManager
from app.services.notificaciones.models import DestinatarioModel


class UsuarioService:
    def __init__(self, db: AsyncSession):
        self.db = db

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
            filtro_para_totalizar_usuarios = fabrica_de_usuarios.obtener_filtro_para_totalizar_usuarios(usuario_actual, company_id, rol)
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

    async def create(self, usuario_actual: Usuario, usuario_in: UsuarioCreate) -> UsuarioOut:
        usuario = await usuario_crud.get_by_field(self.db, "email", usuario_in.email)
        if usuario:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario ya existe")
    
        compania = await CompaniaService(self.db).get_compania(usuario_in.company_id, usuario_actual)
        tipo_documento = await tipo_documento_crud.get(self.db, usuario_in.document_type_id)
        fabrica_de_usuarios = FabricaDeUsuarios.get_user_case(usuario_actual.rol)
        usuario_firebase = fabrica_de_usuarios.obtener_firebase_usuario({
            "usuario_actual": usuario_actual,
            "usuario_nuevo": usuario_in,
            "compania": compania,
            "tipo_documento": tipo_documento
        })

        # crear usuario en firebase
        usuario_firebase = await crear_usuario_firebase(usuario_firebase)
        print("usuario_firebase", usuario_firebase)
        usuario_a_guardar: Usuario = None

        usuario_a_guardar = fabrica_de_usuarios.obtener_usuario_a_guardar({
                "usuario_actual": usuario_actual,
                "usuario_nuevo": usuario_in,
                "firebase_uid": usuario_firebase.uid
            })
        
        notificacion_service = NotificacionService(TipoNotificacion.EMAIL)
        template_manager = TemplateManager()

        notificacion = template_manager.create_notification_from_template(
            template_name='bienvenida_usuario.html',
            destinatarios=[
                DestinatarioModel(
                    email=usuario_a_guardar.email,
                    nombre=usuario_a_guardar.display_name
                )
            ],
            asunto="Bienvenido a Verti-one",
            context={
                "password": usuario_firebase.password,
                "login_link": f"https://verti-one.com"
            }
        )

        resultado = await notificacion_service.enviar_notificacion(notificacion)

        usuario_guardado = await usuario_crud.create(self.db, obj_in=usuario_a_guardar)

        return usuario_guardado
        
        

    async def update(self, uid: str, usuario_in: UsuarioUpdate) -> UsuarioOut:
        usuario = await self.get_by_uid(uid)
        return await usuario_crud.update(self.db, db_obj=usuario, obj_in=usuario_in)

    async def delete(self, uid: str) -> None:
        usuario = await self.get_by_uid(uid)
        return await usuario_crud.remove(self.db, db_obj=usuario)
