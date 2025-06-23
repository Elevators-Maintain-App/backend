from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.db.models.usuarios import Usuario
from app.schemas.unidades import UnidadInDBBase, UnidadCreate, UnidadUpdate, UnidadCreateInDB
from app.db.repositories.unidades import unidad_crud
from app.db.repositories.proyectos import proyecto_crud
from app.db.repositories.tipos_unidad import tipo_unidad_crud
from app.services.unidad.user_cases import FabricaDeUnidades
from app.core.exceptions import ForbiddenException

class UnidadService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, 
                     usuario_actual: Usuario, 
                     skip: Optional[int] = 0, 
                     limit: Optional[int] = None,
                     search: Optional[str] = None,
                     company_id: Optional[str] = None,
                     proyecto_id: Optional[str] = None,
                     tipo_unidad_id: Optional[int] = None,
                     cliente_id: Optional[str] = None) -> List[UnidadInDBBase]:
        try:
            fabrica_de_unidades = FabricaDeUnidades.get_unidad_case(usuario_actual.rol)
            filtros = fabrica_de_unidades.obtener_filtros_para_listar_unidades(
                usuario_actual, search, company_id, proyecto_id, tipo_unidad_id, cliente_id
            )
            
            unidades = await unidad_crud.get_multi_with_advanced_filters(
                self.db, 
                skip=skip, 
                limit=limit, 
                exact_filters=filtros.get("exact_filters", None), 
                ilike_filters=filtros.get("ilike_filters", None), 
                like_filters=filtros.get("like_filters", None)
            )
            
            return [UnidadInDBBase.model_validate(unidad) for unidad in unidades]
        except Exception as e:
            print("**** get_all unidades", e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener las unidades")

    async def get_total_unidades(self, 
                                usuario_actual: Usuario,
                                company_id: Optional[UUID] = None,
                                proyecto_id: Optional[UUID] = None,
                                tipo_unidad_id: Optional[int] = None,
                                cliente_id: Optional[str] = None) -> int:
        try:
            fabrica_de_unidades = FabricaDeUnidades.get_unidad_case(usuario_actual.rol)
            filtro_para_totalizar = fabrica_de_unidades.obtener_filtro_para_totalizar_unidades(
                usuario_actual, company_id, proyecto_id, tipo_unidad_id, cliente_id
            )
            
            cantidad_de_unidades = await unidad_crud.get_total_with_advanced_filters(
                self.db, 
                exact_filters=filtro_para_totalizar.get("exact_filters", None), 
                ilike_filters=filtro_para_totalizar.get("ilike_filters", None), 
                like_filters=filtro_para_totalizar.get("like_filters", None)
            )
            return cantidad_de_unidades
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener la cantidad de unidades")

    async def get_by_id(self, unidad_id: UUID, usuario_actual: Usuario) -> UnidadInDBBase:
        unidad = await unidad_crud.get(self.db, unidad_id)
        if not unidad:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidad no encontrada")
        
        fabrica_de_unidades = FabricaDeUnidades.get_unidad_case(usuario_actual.rol)
        if not fabrica_de_unidades.puede_ver_unidad(usuario_actual, str(unidad_id), unidad.company_id, unidad.proyecto_id, unidad.cliente_id):
            raise ForbiddenException("No tienes permisos para ver esta unidad")
            
        return UnidadInDBBase.model_validate(unidad)

    async def create(self, unidad_in: UnidadCreate, usuario_actual: Usuario) -> UnidadInDBBase:
        fabrica_de_unidades = FabricaDeUnidades.get_unidad_case(usuario_actual.rol)
        if not fabrica_de_unidades.puede_crear_unidades(usuario_actual):
            raise ForbiddenException("No tienes permisos para crear unidades")

        # Determine company_id based on user role
        company_id = usuario_actual.company_id
        
        # Check if unit name already exists in the company
        existente = await unidad_crud.get_by_field(self.db, "nombre", unidad_in.nombre)
        if existente and str(existente.company_id) == str(company_id):
            raise HTTPException(
                status_code=400,
                detail="Ya existe otra unidad con ese nombre en tu compañía"
            )
            
        # Validate project and that it belongs to the company
        proyecto = await proyecto_crud.get(self.db, unidad_in.proyecto_id)
        if not proyecto:
            raise HTTPException(status_code=400, detail="Proyecto no existe")
        if str(proyecto.company_id) != str(company_id):
            raise HTTPException(status_code=400, detail="Proyecto fuera de tu compañía")
            
        cliente_id = proyecto.cliente_id
        if not cliente_id:
            raise HTTPException(status_code=400, detail="El proyecto no tiene cliente asociado")
            
        # Validate unit type
        tipo = await tipo_unidad_crud.get(self.db, unidad_in.tipo_unidad_id)
        if not tipo:
            raise HTTPException(status_code=400, detail="Tipo de unidad no existe")

        # Build payload as schema
        payload = UnidadCreateInDB(
            **unidad_in.dict(exclude_unset=True),
            company_id=company_id,
            cliente_id=cliente_id
        )
        
        return await unidad_crud.create(self.db, obj_in=payload)

    async def update(self, unidad_id: UUID, unidad_in: UnidadUpdate, usuario_actual: Usuario) -> UnidadInDBBase:
        unidad = await unidad_crud.get(self.db, unidad_id)
        if not unidad:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidad no encontrada")
        
        fabrica_de_unidades = FabricaDeUnidades.get_unidad_case(usuario_actual.rol)
        if not fabrica_de_unidades.puede_gestionar_unidades(usuario_actual):
            raise ForbiddenException("No tienes permisos para gestionar unidades")
            
        if not fabrica_de_unidades.puede_ver_unidad(usuario_actual, str(unidad_id), unidad.company_id, unidad.proyecto_id, unidad.cliente_id):
            raise ForbiddenException("No tienes permisos para modificar esta unidad")
            
        return await unidad_crud.update(self.db, db_obj=unidad, obj_in=unidad_in)

    async def delete(self, unidad_id: UUID, usuario_actual: Usuario) -> None:
        unidad = await unidad_crud.get(self.db, unidad_id)
        if not unidad:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidad no encontrada")
        
        fabrica_de_unidades = FabricaDeUnidades.get_unidad_case(usuario_actual.rol)
        if not fabrica_de_unidades.puede_eliminar_unidades(usuario_actual):
            raise ForbiddenException("No tienes permisos para eliminar unidades")
            
        if not fabrica_de_unidades.puede_ver_unidad(usuario_actual, str(unidad_id), unidad.company_id, unidad.proyecto_id, unidad.cliente_id):
            raise ForbiddenException("No tienes permisos para eliminar esta unidad")
            
        await unidad_crud.remove(self.db, unidad_id)

    # Legacy compatibility methods
    async def get_by_company(self, company_id: UUID) -> List[UnidadInDBBase]:
        """Legacy method for backward compatibility"""
        return await unidad_crud.get_multi_by_field(
            self.db,
            field="company_id",
            value=company_id
        )

    async def get_by_id_and_company(self, unidad_id: UUID, company_id: UUID) -> UnidadInDBBase:
        """Legacy method for backward compatibility"""
        unidad = await unidad_crud.get(self.db, unidad_id)
        if not unidad or str(unidad.company_id) != str(company_id):
            raise HTTPException(status_code=404, detail="Unidad no encontrada o fuera de tu compañía")
        return unidad
    
    async def get_total_unidades_por_cliente(self, cliente_id: UUID) -> int:
        """Legacy method for backward compatibility"""
        return await unidad_crud.get_total_by_field(
            self.db,
            field="cliente_id",
            value=cliente_id
        )
    
    async def get_total_unidades_por_proyecto(self, proyecto_id: UUID) -> int:
        """Legacy method for backward compatibility"""
        return await unidad_crud.get_total_by_field(
            self.db,
            field="proyecto_id",
            value=proyecto_id
        ) 