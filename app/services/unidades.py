# app/services/unidades.py

from typing import List, Optional
from uuid import uuid4, UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.usuarios import Usuario
from app.db.models.unidades import Unidad as UnidadModel
from app.db.models.proyectos import Proyecto as ProyectoModel
from app.db.models.clientes import Cliente as ClienteModel
from app.db.models.enums.tipos_unidad import TipoUnidad as TipoUnidadModel
from app.db.repositories.unidades import unidad_crud
from app.db.repositories.proyectos import proyecto_crud
from app.db.repositories.tipos_unidad import tipo_unidad_crud
from app.schemas.comunes import PaginacionResponse
from app.schemas.unidades import (
    UnidadCreate, UnidadUpdate, UnidadInDBBase, UnidadCreateInDB, UnidadListOut
)
from app.services.plans import PlanEnforcementService

class UnidadService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_company(self, company_id: UUID) -> List[UnidadInDBBase]:
        res = await unidad_crud.get_multi_by_field(
            self.db,
            field="company_id",
            value=company_id
        )
        return res

    async def list_company_unidades_out(self, company_id: UUID) -> List[UnidadListOut]:
        stmt = (
            select(
                UnidadModel.id,
                UnidadModel.nombre,
                UnidadModel.kpi_funcionamiento,
                ProyectoModel.nombre.label("proyecto"),
                ClienteModel.nombre.label("cliente"),
                UnidadModel.tipo_unidad_id,
                TipoUnidadModel.nombre.label("tipo_unidad"),
                UnidadModel.company_id,
                UnidadModel.created_at,
                UnidadModel.updated_at,
            )
            .outerjoin(ProyectoModel, UnidadModel.proyecto_id == ProyectoModel.id)
            .outerjoin(ClienteModel, ProyectoModel.cliente_id == ClienteModel.id)
            .outerjoin(TipoUnidadModel, UnidadModel.tipo_unidad_id == TipoUnidadModel.id)
            .where(UnidadModel.company_id == company_id)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            UnidadListOut(
                id=row.id,
                nombre=row.nombre,
                kpi_funcionamiento=row.kpi_funcionamiento,
                proyecto=row.proyecto if row.proyecto else "—",
                cliente=row.cliente if row.cliente else "—",
                tipo_unidad_id=row.tipo_unidad_id,
                tipo_unidad=row.tipo_unidad if row.tipo_unidad else "—",
                company_id=row.company_id,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]

    async def get_by_id_and_company(self, unidad_id: UUID, company_id: UUID) -> UnidadInDBBase:
        unidad = await unidad_crud.get(self.db, unidad_id)
        if not unidad or str(unidad.company_id) != str(company_id):
            raise HTTPException(status_code=404, detail="Unidad no encontrada o fuera de tu compañía")
        return unidad
    
    async def get_total_unidades_por_compania(self, company_id: UUID) -> int:
        total = await unidad_crud.get_total_by_field(
            self.db,
            field="company_id",
            value=company_id
        )
        return total
    
    async def get_total_unidades_por_cliente(self, cliente_id: UUID) -> int:
        total = await unidad_crud.get_total_by_field(
            self.db,
            field="cliente_id",
            value=cliente_id
        )
        return total
    
    async def get_total_unidades_por_proyecto(self, proyecto_id: UUID) -> int:
        total = await unidad_crud.get_total_by_field(
            self.db,
            field="proyecto_id",
            value=proyecto_id
        )
        return total

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

        plan_enforcement = PlanEnforcementService(self.db)
        await plan_enforcement.assert_can_create_unit(company_id)

        # Reconstruir payload como schema
        payload = UnidadCreateInDB(
            **unidad_in.dict(exclude_unset=True),
            company_id=company_id,
            cliente_id=str(cliente_id)
        )
        created = await unidad_crud.create(self.db, obj_in=payload)
        await plan_enforcement.refresh_current_usage_snapshot(company_id)
        return created

    async def update(self, unidad_id: UUID, unidad_in: UnidadUpdate, company_id: UUID) -> UnidadInDBBase:
        unidad = await unidad_crud.get(self.db, unidad_id)
        if not unidad or unidad.company_id != company_id:
            raise HTTPException(status_code=404, detail="Unidad no encontrada o fuera de tu compañía")
        updated = await unidad_crud.update(self.db, db_obj=unidad, obj_in=unidad_in)
        return updated

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
        company_id: Optional[UUID] = None,
        proyecto_id: Optional[UUID] = None
    ) -> PaginacionResponse[UnidadListOut]:
        try:
            # Normalizar rol (soporta Enum .name/.value o string plano)
            raw_role = getattr(usuario_actual, "rol", None)
            role_norm = None
            if raw_role is None:
                role_norm = None
            elif hasattr(raw_role, "name"):
                role_norm = raw_role.name.lower()
            elif hasattr(raw_role, "value"):
                role_norm = str(raw_role.value).lower()
            else:
                role_norm = str(raw_role).split(".")[-1].lower()

            exact_filters: dict = {}
            ilike_filters: dict = {}

            # Restricción por rol (ya normalizado)
            if role_norm in ("admin", "supervisor"):
                exact_filters["company_id"] = getattr(usuario_actual, "company_id", None)
            elif company_id:
                exact_filters["company_id"] = company_id

            # Validación y filtro por proyecto_id
            if proyecto_id is not None:
                # Validar que el proyecto existe
                proyecto = await proyecto_crud.get(self.db, proyecto_id)
                if not proyecto:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Proyecto no encontrado"
                    )
                
                # Validar que el proyecto pertenece a la compañía correcta según el rol
                expected_company_id = None
                if role_norm in ("admin", "supervisor"):
                    expected_company_id = getattr(usuario_actual, "company_id", None)
                elif company_id:
                    expected_company_id = company_id
                
                if expected_company_id and str(proyecto.company_id) != str(expected_company_id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="El proyecto no pertenece a tu compañía"
                    )
                
                # Aplicar filtro por proyecto_id
                exact_filters["proyecto_id"] = proyecto_id

            # Búsqueda por nombre
            if search:
                ilike_filters["nombre"] = search

            # Consulta paginada aplicando filtros
            unidades = await unidad_crud.get_multi_with_advanced_filters(
                self.db,
                skip=skip,
                limit=limit,
                exact_filters=exact_filters or None,
                ilike_filters=ilike_filters or None
            )


            total = await unidad_crud.get_total_with_advanced_filters(
                self.db,
                exact_filters=exact_filters or None,
                ilike_filters=ilike_filters or None
            )

            return PaginacionResponse(data=unidades, total=total, skip=skip, limit=limit)

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
