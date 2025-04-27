# app/services/unidades.py

from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.unidades import unidad_crud
from app.db.repositories.proyectos import proyecto_crud
from app.db.repositories.tipos_unidad import tipo_unidad_crud
from app.schemas.unidades import UnidadCreate, UnidadUpdate, UnidadInDBBase

class UnidadService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[UnidadInDBBase]:
        return await unidad_crud.get_multi(self.db)

    async def get_by_id(self, unidad_id: UUID) -> UnidadInDBBase:
        unidad = await unidad_crud.get(self.db, unidad_id)
        if not unidad:
            raise HTTPException(status_code=404, detail="Unidad no encontrada")
        return unidad

    async def create(self, unidad_in: UnidadCreate) -> UnidadInDBBase:
        # Validar existencia de proyecto
        proyecto = await proyecto_crud.get(self.db, unidad_in.proyecto_id)
        if not proyecto:
            raise HTTPException(status_code=400, detail="El proyecto especificado no existe.")

        # Validar existencia de tipo de unidad
        tipo_unidad = await tipo_unidad_crud.get(self.db, unidad_in.tipo_unidad_id)
        if not tipo_unidad:
            raise HTTPException(status_code=400, detail="El tipo de unidad especificado no existe.")

        return await unidad_crud.create(self.db, obj_in=unidad_in)

    async def update(self, unidad_id: UUID, unidad_in: UnidadUpdate) -> UnidadInDBBase:
        unidad_db = await unidad_crud.get(self.db, unidad_id)
        if not unidad_db:
            raise HTTPException(status_code=404, detail="Unidad no encontrada")

        return await unidad_crud.update(self.db, db_obj=unidad_db, obj_in=unidad_in)

    async def delete(self, unidad_id: UUID) -> None:
        unidad_db = await unidad_crud.get(self.db, unidad_id)
        if not unidad_db:
            raise HTTPException(status_code=404, detail="Unidad no encontrada")

        await unidad_crud.remove(self.db, unidad_id)
