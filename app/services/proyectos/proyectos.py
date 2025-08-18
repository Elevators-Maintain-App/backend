# app/services/proyectos.py

from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.proyectos import Proyecto
from app.db.models.usuarios import Usuario
from app.db.repositories.proyectos import proyecto_crud
from app.db.repositories.zonas_geograficas import zona_geografica_crud
from app.schemas.proyectos import ProyectoCreate, ProyectoUpdate, ProyectoInDBBase, ProyectoCreateInDB
from app.services.proyectos.user_cases import FabricaDeProyectos
from app.schemas.comunes import PaginacionResponse
from app.schemas.proyectos import ProyectoOut
from app.services.proyectos.proyectos_mappers import map_proyecto_to_proyecto_out
from app.auth.firebase import FirebaseUser

class ProyectoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, usuario_actual: Usuario, skip: Optional[int] = 0, limit: Optional[int] = None, search: Optional[str] = None, company_id: Optional[str] = None, cliente_id: Optional[str] = None) -> List[ProyectoInDBBase]:
        try:
            fabrica_de_proyectos = FabricaDeProyectos.get_proyecto_case(usuario_actual.rol)
            filtros = fabrica_de_proyectos.obtener_filtros_para_listar_proyectos(usuario_actual, search, company_id, cliente_id)
            proyectos = await proyecto_crud.get_multi_with_advanced_filters(
                self.db, 
                skip=skip, 
                limit=limit, 
                exact_filters=filtros.get("exact_filters", None), 
                ilike_filters=filtros.get("ilike_filters", None), 
                like_filters=filtros.get("like_filters", None)
            )            
            return proyectos
        except Exception as e:
            print("**** get_all proyectos", e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener los proyectos")
        
    async def get_total_proyectos(self, usuario_actual: Usuario, company_id: Optional[UUID] = None, cliente_id: Optional[str] = None) -> int:
        try:
            fabrica_de_proyectos = FabricaDeProyectos.get_proyecto_case(usuario_actual.rol)
            filtro_para_totalizar_proyectos = fabrica_de_proyectos.obtener_filtro_para_totalizar_proyectos(usuario_actual, company_id, cliente_id)
            cantidad_de_proyectos = await proyecto_crud.get_total_with_advanced_filters(
                self.db, 
                exact_filters=filtro_para_totalizar_proyectos.get("exact_filters", None), 
                ilike_filters=filtro_para_totalizar_proyectos.get("ilike_filters", None), 
                like_filters=filtro_para_totalizar_proyectos.get("like_filters", None)
            )
            return cantidad_de_proyectos
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener la cantidad de proyectos")

    async def get_all_basic(self) -> List[ProyectoInDBBase]:
        """
        Método básico para obtener todos los proyectos sin filtros (para compatibilidad con versiones anteriores)
        """
        return await proyecto_crud.get_multi(self.db)

    async def get_by_id(self, proyecto_id: UUID) -> Proyecto:
        proyecto = await proyecto_crud.get_with_relationships(self.db, proyecto_id)
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        return proyecto 

    async def get_by_company(self, company_id: UUID) -> List[ProyectoInDBBase]:
        """
        Lista los proyectos de una compañía dada.
        """
        return await proyecto_crud.get_multi_by_field(
            self.db,
            field="company_id",
            value=company_id
        )
    
    async def get_proyectos_by_cliente(self, cliente_id: UUID) -> List[ProyectoInDBBase]:
        return await proyecto_crud.get_multi_by_field(
            self.db,
            field="cliente_id",
            value=cliente_id
        )
    
    async def get_by_id_and_company(self, proyecto_id: UUID, company_id: UUID):
        proyecto = await proyecto_crud.get(self.db, proyecto_id)
        if not proyecto or proyecto.company_id != company_id:
            raise HTTPException(404, "Proyecto no encontrado o fuera de tu compañía.")
        return proyecto

    async def create(
        self,
        proyecto_in: ProyectoCreate,
        user: FirebaseUser
    ) -> ProyectoInDBBase:
        fabrica_de_proyectos = FabricaDeProyectos.get_proyecto_case(user.rol)
        proyecto_payload = fabrica_de_proyectos.obtener_payload_para_crear_proyecto(proyecto_in, user)

        return await proyecto_crud.create(self.db, obj_in=proyecto_payload)

    async def update(
        self,
        proyecto_id: UUID,
        proyecto_in: ProyectoUpdate,
        user: FirebaseUser
    ) -> ProyectoInDBBase:
        proyecto = await proyecto_crud.get(self.db, proyecto_id)
        if not proyecto or proyecto.company_id != user.company_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado o fuera de tu compañía."
            )
        
        return await proyecto_crud.update(self.db, db_obj=proyecto, obj_in=proyecto_in)

    async def delete(self, proyecto_id: UUID, company_id: UUID) -> None:
        proyecto = await proyecto_crud.get(self.db, proyecto_id)
        if not proyecto or proyecto.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado o fuera de tu compañía."
            )
        await proyecto_crud.remove(self.db, proyecto_id)


    async def get_proyectos_con_paginacion(
        self,
        usuario_actual: Usuario,
        skip: Optional[int] = 0,
        limit: Optional[int] = 20,
        search: Optional[str] = None,
        company_id: Optional[str] = None,
        cliente_id: Optional[str] = None,
    ) -> PaginacionResponse[ProyectoOut]:
        """
        Obtiene proyectos con filtros basados en el rol del usuario.
        """
        try:
            fabrica_de_proyectos = FabricaDeProyectos.get_proyecto_case(usuario_actual.rol)
            filtros = fabrica_de_proyectos.obtener_filtros_para_listar_proyectos(
                usuario_actual,
                search,
                company_id,
                cliente_id,
            )
            
            proyectos = await proyecto_crud.get_multi_with_advanced_filters(
                self.db,
                skip=skip,
                limit=limit,
                exact_filters=filtros.get("exact_filters", None),
                ilike_filters=filtros.get("ilike_filters", None),
                like_filters=filtros.get("like_filters", None),
            )

            proyectos_out = [map_proyecto_to_proyecto_out(proyecto) for proyecto in proyectos]

            total = await proyecto_crud.get_total_with_advanced_filters(
                self.db,
                exact_filters=filtros.get("exact_filters", None),
                ilike_filters=filtros.get("ilike_filters", None),
                like_filters=filtros.get("like_filters", None),
            )
        
            return PaginacionResponse(
                data=proyectos_out,
                total=total,
                skip=skip,
                limit=limit,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener los proyectos",
            )