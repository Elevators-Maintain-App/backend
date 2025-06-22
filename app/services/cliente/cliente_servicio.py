# app/services/clientes.py

from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.clientes import cliente_crud
from app.db.repositories.proyectos import proyecto_crud
from app.db.repositories.unidades import unidad_crud
from app.db.repositories.ordenes_de_trabajo import orden_de_trabajo_crud

from app.schemas.clientes import ClienteCreate, ClienteUpdate, ClienteOut
from app.schemas.proyectos import ProyectoInDBBase
from app.schemas.unidades import UnidadInDBBase
from app.schemas.ordenes_de_trabajo import OrdenDeTrabajoInDBBase
from app.auth.firebase import FirebaseUser
from app.db.models.usuarios import Usuario
from app.services.cliente.cliente_mapper import cliente_to_cliente_out
from app.services.cliente.user_cases import FabricaDeClientes
from app.core.exceptions import ForbiddenException
from app.schemas.comunes import PaginacionResponse

class ClienteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_clientes_con_paginacion(self, usuario_actual: Usuario, skip: Optional[int] = 0, limit: Optional[int] = None, search: Optional[str] = None, company_id: Optional[str] = None, tipo_documento_id: Optional[int] = None) -> PaginacionResponse[ClienteOut]:
        """
        Obtiene clientes con filtros basados en el rol del usuario
        """
        try:
            fabrica_de_clientes = FabricaDeClientes.get_cliente_case(usuario_actual.rol)
            filtros = fabrica_de_clientes.obtener_filtros_para_listar_clientes(usuario_actual, search, company_id, tipo_documento_id)
            
            clientes = await cliente_crud.get_multi_with_advanced_filters_and_relations(
                self.db, 
                skip=skip, 
                limit=limit, 
                exact_filters=filtros.get("exact_filters", None), 
                ilike_filters=filtros.get("ilike_filters", None), 
                like_filters=filtros.get("like_filters", None)
            )
            total_clientes = await self._total_clientes_con_filtro(filtros)
            
            return PaginacionResponse(
                data=[cliente_to_cliente_out(cliente) for cliente in clientes],
                total=total_clientes,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            print("**** get_all clientes", e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener los clientes")

    async def _total_clientes_con_filtro(self, filtros: dict) -> int:
        cantidad_de_clientes = await cliente_crud.get_total_with_advanced_filters(
            self.db, 
            exact_filters=filtros.get("exact_filters", None), 
            ilike_filters=filtros.get("ilike_filters", None), 
            like_filters=filtros.get("like_filters", None)
        )
        return cantidad_de_clientes

    async def get_total_clientes(self, usuario_actual: Usuario, company_id: Optional[UUID] = None, tipo_documento_id: Optional[int] = None) -> int:
        """
        Obtiene el total de clientes basado en los permisos del usuario
        """
        try:
            fabrica_de_clientes = FabricaDeClientes.get_cliente_case(usuario_actual.rol)
            filtro_para_totalizar_clientes = fabrica_de_clientes.obtener_filtro_para_totalizar_clientes(usuario_actual, company_id, tipo_documento_id)
            
            cantidad_de_clientes = await cliente_crud.get_total_with_advanced_filters(
                self.db, 
                exact_filters=filtro_para_totalizar_clientes.get("exact_filters", None), 
                ilike_filters=filtro_para_totalizar_clientes.get("ilike_filters", None), 
                like_filters=filtro_para_totalizar_clientes.get("like_filters", None)
            )
            return cantidad_de_clientes
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener la cantidad de clientes")

    async def get_all_basic(self, usuario_actual: FirebaseUser) -> List[ClienteOut]:
        """
        Método básico para obtener clientes (para compatibilidad con versiones anteriores)
        """
        clientes = await cliente_crud.get_multi(self.db)
        return [cliente_to_cliente_out(cliente) for cliente in clientes]

    async def get_by_id(self, cliente_id: UUID, usuario_actual: Usuario) -> ClienteOut:        
        """
        Obtiene un cliente por su ID basado en los permisos del usuario
        """
        fabrica_de_clientes = FabricaDeClientes.get_cliente_case(usuario_actual.rol)
        
        cliente = await cliente_crud.get_cliente_con_relaciones(self.db, cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        if not fabrica_de_clientes.puede_ver_cliente(usuario_actual, str(cliente_id), cliente.compania_id):
            raise ForbiddenException("No tienes permisos para ver este cliente")
        
        return cliente_to_cliente_out(cliente)

    async def create_cliente(self, cliente_in: ClienteCreate, usuario_actual: Usuario) -> ClienteOut:
        """
        Crea un nuevo cliente basado en los permisos del usuario
        """
        fabrica_de_clientes = FabricaDeClientes.get_cliente_case(usuario_actual.rol)
        
        if not fabrica_de_clientes.puede_crear_clientes(usuario_actual=usuario_actual, compania_id=cliente_in.compania_id):
            raise ForbiddenException("No tienes permisos para crear clientes")
        
        return await cliente_crud.create(self.db, obj_in=cliente_in)

    async def update_cliente(self, cliente_id: UUID, cliente_in: ClienteUpdate, usuario_actual: Usuario) -> ClienteOut:
        """
        Actualiza un cliente basado en los permisos del usuario
        """
        fabrica_de_clientes = FabricaDeClientes.get_cliente_case(usuario_actual.rol)
        
        if not fabrica_de_clientes.puede_gestionar_clientes(usuario_actual):
            raise ForbiddenException("No tienes permisos para actualizar clientes")
        
        cliente_db = await cliente_crud.get_cliente_con_relaciones(self.db, cliente_id)
        if not cliente_db:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        if not fabrica_de_clientes.puede_ver_cliente(usuario_actual, str(cliente_id), cliente_db.compania_id):
            raise ForbiddenException("No tienes permisos para actualizar este cliente")

        return await cliente_crud.update(self.db, db_obj=cliente_db, obj_in=cliente_in)

    async def delete_cliente(self, cliente_id: UUID, usuario_actual: Usuario) -> None:
        """
        Elimina un cliente basado en los permisos del usuario
        """
        fabrica_de_clientes = FabricaDeClientes.get_cliente_case(usuario_actual.rol)
        
        if not fabrica_de_clientes.puede_eliminar_clientes(usuario_actual):
            raise ForbiddenException("No tienes permisos para eliminar clientes")
        
        cliente_db = await cliente_crud.get_cliente_con_relaciones(self.db, cliente_id)
        if not cliente_db:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        if not fabrica_de_clientes.puede_ver_cliente(usuario_actual, str(cliente_id), cliente_db.compania_id):
            raise ForbiddenException("No tienes permisos para eliminar este cliente")

        await cliente_crud.remove(self.db, cliente_id)

    # Métodos especiales:
    async def get_proyectos(self, cliente_id: UUID) -> List[ProyectoInDBBase]:
        proyectos = await proyecto_crud.get_multi_by_field(self.db, field="cliente_id", value=cliente_id)
        return proyectos

    async def get_unidades(self, cliente_id: UUID) -> List[UnidadInDBBase]:
        proyectos = await proyecto_crud.get_multi_by_field(self.db, field="cliente_id", value=cliente_id)
        if not proyectos:
            return []
        
        proyecto_ids = [proyecto.id for proyecto in proyectos]
        unidades = await unidad_crud.get_multi_by_fields(self.db, field="proyecto_id", values=proyecto_ids)
        return unidades

    async def get_ordenes_trabajo(self, cliente_id: UUID) -> List[OrdenDeTrabajoInDBBase]:
        proyectos = await proyecto_crud.get_multi_by_field(self.db, field="cliente_id", value=cliente_id)
        if not proyectos:
            return []
        
        proyecto_ids = [proyecto.id for proyecto in proyectos]
        unidades = await unidad_crud.get_multi_by_fields(self.db, field="proyecto_id", values=proyecto_ids)
        if not unidades:
            return []
        
        unidad_ids = [unidad.id for unidad in unidades]
        ordenes = await orden_de_trabajo_crud.get_multi_by_fields(self.db, field="unidad_id", values=unidad_ids)
        return ordenes
