# app/services/supervisores.py

from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.supervisores import supervisor_crud
from app.db.repositories.ordenes_de_trabajo import orden_de_trabajo_crud
from app.schemas.supervisores import SupervisorCreate, SupervisorUpdate, SupervisorInDBBase
from app.schemas.ordenes_de_trabajo import OrdenDeTrabajoInDBBase

class SupervisorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[SupervisorInDBBase]:
        return await supervisor_crud.get_multi(self.db)

    async def get_by_id(self, supervisor_id: UUID) -> SupervisorInDBBase:
        supervisor = await supervisor_crud.get(self.db, supervisor_id)
        if not supervisor:
            raise HTTPException(status_code=404, detail="Supervisor no encontrado")
        return supervisor

    async def create(self, supervisor_in: SupervisorCreate) -> SupervisorInDBBase:
        # Validar unicidad de nombre
        existing_nombre = await supervisor_crud.get_by_field(self.db, field="nombre", value=supervisor_in.nombre)
        if existing_nombre:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un supervisor con este nombre."
            )

        return await supervisor_crud.create(self.db, obj_in=supervisor_in)

    async def update(self, supervisor_id: UUID, supervisor_in: SupervisorUpdate) -> SupervisorInDBBase:
        supervisor_db = await supervisor_crud.get(self.db, supervisor_id)
        if not supervisor_db:
            raise HTTPException(status_code=404, detail="Supervisor no encontrado")

        return await supervisor_crud.update(self.db, db_obj=supervisor_db, obj_in=supervisor_in)

    async def delete(self, supervisor_id: UUID) -> None:
        supervisor_db = await supervisor_crud.get(self.db, supervisor_id)
        if not supervisor_db:
            raise HTTPException(status_code=404, detail="Supervisor no encontrado")

        await supervisor_crud.remove(self.db, supervisor_id)

     # Método especial:

    async def get_ordenes_trabajo(self, supervisor_id: UUID) -> List[OrdenDeTrabajoInDBBase]:
        ordenes = await orden_de_trabajo_crud.get_multi_by_field(self.db, field="supervisor_id", value=supervisor_id)
        return ordenes