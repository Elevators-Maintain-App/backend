# app/services/proyectos.py

from typing import List
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.proyectos import Proyecto
from app.db.repositories.proyectos import proyecto_crud
from app.db.repositories.zonas_geograficas import zona_geografica_crud
from app.schemas.proyectos import ProyectoCreate, ProyectoUpdate, ProyectoInDBBase, ProyectoCreateInDB

class ProyectoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[ProyectoInDBBase]:
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
