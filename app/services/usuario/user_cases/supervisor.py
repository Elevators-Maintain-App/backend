from dataclasses import dataclass
from fastapi import HTTPException
from app.services.usuario.interfaces import CrearUsuarioFirebaseParams, CrearUsuarioParams
from app.db.models.compania import Compania
from app.db.models.usuarios import Usuario, Rol
from app.schemas.usuarios import UsuarioCreate
from app.auth.firebase import FirebaseUser
from app.db.models import TipoDocumento
from typing import Optional
from uuid import UUID
from .base_usuario import BaseUsuario
from app.db.models.clientes import Cliente

class SupervisorCase(BaseUsuario):
    def obtener_firebase_usuario(self, params: CrearUsuarioFirebaseParams) -> FirebaseUser:
        usuario_actual: Usuario = params.usuario_actual
        usuario_nuevo: UsuarioCreate = params.usuario_nuevo
        compania: Compania = params.compania
        tipo_documento: TipoDocumento = params.tipo_documento
        cliente: Cliente | None = params.cliente

        if usuario_actual.rol not in [Rol.SUPERVISOR]:
            raise HTTPException(status_code=403, detail="No tienes permisos para crear usuarios")

        if usuario_nuevo.rol not in [Rol.TECHNICIAN]:
            raise HTTPException(status_code=403, detail="No tienes permisos para crear usuarios")
        
        return self.mapear_usuario_dto_a_usuario_firebase(usuario_nuevo, compania, tipo_documento, cliente)
    
    def validar_y_normalizar_company_id(self, usuario_actual: Usuario, company_id: Optional[UUID]) -> UUID:
        """
        Valida y normaliza el company_id para supervisor.
        Si no se proporciona company_id, usa el del supervisor.
        Valida que el supervisor tenga company_id asignado.
        """
        if usuario_actual.rol not in [Rol.SUPERVISOR]:
            raise HTTPException(status_code=403, detail="No tienes permisos para crear usuarios")
        
        if company_id is None:
            # Usar el company_id del supervisor
            if usuario_actual.company_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="El usuario supervisor no tiene company_id asignado"
                )
            return usuario_actual.company_id
        else:
            # Validar que el company_id proporcionado coincida con el del supervisor (seguridad)
            if usuario_actual.company_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="El usuario supervisor no tiene company_id asignado"
                )
            if company_id != usuario_actual.company_id:
                raise HTTPException(
                    status_code=403,
                    detail="No puedes crear usuarios en otra compañía"
                )
            return company_id
    
    def obtener_usuario_a_guardar(self, params: CrearUsuarioParams) -> Usuario:
        usuario_actual: Usuario = params.usuario_actual
        usuario_nuevo: UsuarioCreate = params.usuario_nuevo
        firebase_uid: str = params.firebase_uid
        
        if usuario_actual.rol not in [Rol.SUPERVISOR]:
            raise HTTPException(status_code=403, detail="No tienes permisos para crear usuarios")
        
        if usuario_nuevo.rol not in [Rol.TECHNICIAN]:
            raise HTTPException(status_code=403, detail="No tienes permisos para crear usuarios")
        
        usuario = self.mapear_usuario_dto_a_usuario_create(usuario_nuevo, firebase_uid)
        # El company_id ya viene normalizado desde validar_y_normalizar_company_id

        return usuario
    
    def obtener_filtros_para_listar_usuarios(self, usuario_actual: Usuario, search: Optional[str], company_id: Optional[str], rol: Optional[str]) -> dict:
        filters = {
            "exact_filters": {
                "company_id": usuario_actual.company_id,
                "rol": Rol.TECHNICIAN.name
            },
            "ilike_filters": {},
            "like_filters": {}
        }
        if search:
            filters["ilike_filters"]["display_name"] = f"%{search}%"

        return filters 


    def obtener_filtro_para_totalizar_usuarios(self, usuario_actual: Usuario, company_id: Optional[UUID], rol: Optional[Rol]) -> dict:
        compania_id =  usuario_actual.company_id
        filters = {
            "exact_filters": {
                "company_id": compania_id,
            },
            "ilike_filters": {},
            "like_filters": {}
        }

        if rol:
            filters["exact_filters"]["rol"] = rol

        return filters