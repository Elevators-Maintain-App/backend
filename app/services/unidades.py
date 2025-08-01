# app/services/unidades.py

from typing import List, Optional
from uuid import uuid4, UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.usuarios import Usuario
from app.db.repositories.unidades import unidad_crud
from app.db.repositories.proyectos import proyecto_crud
from app.db.repositories.tipos_unidad import tipo_unidad_crud
from app.schemas.comunes import PaginacionResponse
from app.schemas.unidades import UnidadCreate, UnidadUpdate, UnidadInDBBase, UnidadCreateInDB, UnidadListOut

class UnidadService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_company(self, company_id: UUID) -> List[UnidadInDBBase]:
        return await unidad_crud.get_multi_by_field(
            self.db,
            field="company_id",
            value=company_id
        )

    async def get_by_id_and_company(self, unidad_id: UUID, company_id: UUID) -> UnidadInDBBase:
        unidad = await unidad_crud.get(self.db, unidad_id)
        if not unidad or str(unidad.company_id) != str(company_id):
            raise HTTPException(status_code=404, detail="Unidad no encontrada o fuera de tu compañía")
        return unidad
    
    async def get_total_unidades_por_compania(self, company_id: UUID) -> int:
        return await unidad_crud.get_total_by_field(
            self.db,
            field="company_id",
            value=company_id
        )
    
    async def get_total_unidades_por_cliente(self, cliente_id: UUID) -> int:
        return await unidad_crud.get_total_by_field(
            self.db,
            field="cliente_id",
            value=cliente_id
        )
    
    async def get_total_unidades_por_proyecto(self, proyecto_id: UUID) -> int:
        return await unidad_crud.get_total_by_field(
            self.db,
            field="proyecto_id",
            value=proyecto_id
        )

    async def create(self, unidad_in: UnidadCreate, company_id: UUID) -> UnidadInDBBase:
        existente = await unidad_crud.get_by_field(self.db, "nombre", unidad_in.nombre)
        if existente and str(existente.company_id) == str(company_id):
            raise HTTPException(
                status_code=400,
                detail="Ya existe otra unidad con ese nombre en tu compañía"
            )
        # validar proyecto y que pertenezca a la compañía
        proyecto = await proyecto_crud.get(self.db, unidad_in.proyecto_id)
        if not proyecto:
            raise HTTPException(status_code=400, detail="Proyecto no existe")
        if str(proyecto.company_id) != str(company_id):
            raise HTTPException(status_code=400, detail="Proyecto fuera de tu compañía")
        cliente_id = proyecto.cliente_id
        if not cliente_id:
            raise HTTPException(status_code=400, detail="El proyecto no tiene cliente asociado")
        # validar tipo de unidad
        tipo = await tipo_unidad_crud.get(self.db, unidad_in.tipo_unidad_id)
        if not tipo:
            raise HTTPException(status_code=400, detail="Tipo de unidad no existe")

        # Reconstruir payload como schema
        payload = UnidadCreateInDB(
            **unidad_in.dict(exclude_unset=True),
            company_id=company_id,
            cliente_id=cliente_id
        )
        return await unidad_crud.create(self.db, obj_in=payload)

    async def update(self, unidad_id: UUID, unidad_in: UnidadUpdate, company_id: UUID) -> UnidadInDBBase:
        unidad = await unidad_crud.get(self.db, unidad_id)
        if not unidad or unidad.company_id != company_id:
            raise HTTPException(status_code=404, detail="Unidad no encontrada o fuera de tu compañía")
        return await unidad_crud.update(self.db, db_obj=unidad, obj_in=unidad_in)

    async def delete(self, unidad_id: UUID, company_id: UUID) -> None:
        unidad = await unidad_crud.get(self.db, unidad_id)
        if not unidad or unidad.company_id != company_id:
            raise HTTPException(status_code=404, detail="Unidad no encontrada o fuera de tu compañía")
        await unidad_crud.remove(self.db, unidad_id)

    async def get_unidades_con_paginacion(
        self,
        usuario_actual: Usuario,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        company_id: Optional[UUID] = None
    ) -> PaginacionResponse[UnidadListOut]:
        """
        Lista de unidades con paginación filtrados por permisos del usuario.
        superAdmin: ve todas las unidades
        admin / supervisor: ve las unidades de su compañía
        """
        try: 
            exact_filters = {}
            ilike_filters = {}

            #Restricciones por rol
            if usuario_actual.rol in ("admin", "supervisor"):
                exact_filters["company_id"] = str(usuario_actual.company_id)
            elif company_id:
                exact_filters["company_id"] = str(company_id)

            #Busqueda por nombre
            if search:
                ilike_filters["nombre"] = f"%{search}%"

            unidades = await unidad_crud.get_multi(
                self.db,
                skip=skip,
                limit=limit,
            )
            total = await unidad_crud.get_total_with_advanced_filters(
                self.db,
                exact_filters=exact_filters,
                ilike_filters=ilike_filters
            )
            return PaginacionResponse(
                data=unidades,
                total=total,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            import traceback, sys
            traceback.print_exc(file=sys.stdout)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )