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
from app.services.proyecto.user_cases import FabricaDeProyectos
from app.schemas.comunes import PaginacionResponse
from app.schemas.proyectos import ProyectoOut

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

    async def get_by_id(self, proyecto_id: UUID) -> ProyectoInDBBase:
        proyecto = await proyecto_crud.get(self.db, proyecto_id)
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
        company_id: UUID
    ) -> ProyectoInDBBase:
        # 1) Validar zona geográfica
        if proyecto_in.zona_geografica_id:
            zona = await zona_geografica_crud.get(
                self.db, proyecto_in.zona_geografica_id
            )
            if not zona:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La zona geográfica especificada no existe."
                )

        # 2) Validar unicidad de nombre por compañía
        existing = await proyecto_crud.get_multi_by_filters(
            self.db,
            filters=[
                Proyecto.company_id == company_id,
                Proyecto.nombre       == proyecto_in.nombre
            ],
            skip=0,
            limit=1
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un proyecto con este nombre en tu compañía."
            )

        # 3) Crear proyecto incluyendo company_id
        proyecto_payload = ProyectoCreateInDB(
        **proyecto_in.dict(exclude_unset=True),
        company_id=company_id
        )
        return await proyecto_crud.create(self.db, obj_in=proyecto_payload)

    async def update(
        self,
        proyecto_id: UUID,
        proyecto_in: ProyectoUpdate,
        company_id: UUID
    ) -> ProyectoInDBBase:
        proyecto = await proyecto_crud.get(self.db, proyecto_id)
        if not proyecto or proyecto.company_id != company_id:
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
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        company_id: Optional[UUID] = None,
    ) -> PaginacionResponse[ProyectoOut]:
        """
        Lista proyectos filtrados por permisos del usuario.
        - superAdmin: ve todos (opcionalmente filtra por company_id)
        - admin / supervisor: solo los de su compañía
        """
        try:
            exact_filters = {}
            ilike_filters = {}

            # Restricciones por rol
            if usuario_actual.rol in ("admin", "supervisor"):
                exact_filters["compania_id"] = str(usuario_actual.compania_id)
            elif company_id:
                exact_filters["compania_id"] = str(company_id)

            # Búsqueda por nombre
            if search:
                ilike_filters["nombre"] = f"%{search}%"

            proyectos = await proyecto_crud.get_multi(
                self.db,
                skip=skip,
                limit=limit,  
            )
            total = await proyecto_crud.get_total_with_advanced_filters(
                self.db,
                exact_filters=exact_filters or None,
                ilike_filters=ilike_filters or None,
            )
            return PaginacionResponse(
                data=proyectos,
                total=total,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            import traceback, sys
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)            # opcional: devuelve el mensaje real
            )