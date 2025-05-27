# app/services/zonas_geograficas.py

from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.zonas_geograficas import zona_geografica_crud
from app.schemas.zonas_geograficas import ZonaGeograficaCreate, ZonaGeograficaUpdate, ZonaGeograficaInDBBase

class ZonaGeograficaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[ZonaGeograficaInDBBase]:
        return await zona_geografica_crud.get_multi(self.db)

    async def get_by_id(self, zona_id: UUID) -> ZonaGeograficaInDBBase:
        zona = await zona_geografica_crud.get(self.db, zona_id)
        if not zona:
            raise HTTPException(status_code=404, detail="Zona geográfica no encontrada")
        return zona

    async def create(self, zona_in: ZonaGeograficaCreate) -> ZonaGeograficaInDBBase:
        # Validar unicidad de nombre
        existing_zona = await zona_geografica_crud.get_by_field(self.db, field="nombre", value=zona_in.nombre)
        if existing_zona:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una zona geográfica con este nombre."
            )

        return await zona_geografica_crud.create(self.db, obj_in=zona_in)

    async def update(self, zona_id: UUID, zona_in: ZonaGeograficaUpdate) -> ZonaGeograficaInDBBase:
        zona_db = await zona_geografica_crud.get(self.db, zona_id)
        if not zona_db:
            raise HTTPException(status_code=404, detail="Zona geográfica no encontrada")

        return await zona_geografica_crud.update(self.db, db_obj=zona_db, obj_in=zona_in)

    async def delete(self, zona_id: UUID) -> None:
        zona_db = await zona_geografica_crud.get(self.db, zona_id)
        if not zona_db:
            raise HTTPException(status_code=404, detail="Zona geográfica no encontrada")

        await zona_geografica_crud.remove(self.db, zona_id)
