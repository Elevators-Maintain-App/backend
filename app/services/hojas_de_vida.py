# app/services/hojas_de_vida.py

from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.hojas_de_vida import hoja_de_vida_crud
from app.db.repositories.unidades import unidad_crud
from app.schemas.hojas_de_vida import HojaDeVidaCreate, HojaDeVidaUpdate, HojaDeVidaInDBBase

class HojaDeVidaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[HojaDeVidaInDBBase]:
        return await hoja_de_vida_crud.get_multi(self.db)

    async def get_by_id(self, hoja_id: UUID) -> HojaDeVidaInDBBase:
        hoja = await hoja_de_vida_crud.get(self.db, hoja_id)
        if not hoja:
            raise HTTPException(status_code=404, detail="Hoja de vida no encontrada")
        return hoja

    async def create(self, hoja_in: HojaDeVidaCreate) -> HojaDeVidaInDBBase:
        # Validar existencia de unidad
        unidad = await unidad_crud.get(self.db, hoja_in.unidad_id)
        if not unidad:
            raise HTTPException(status_code=400, detail="La unidad especificada no existe.")

        return await hoja_de_vida_crud.create(self.db, obj_in=hoja_in)

    async def update(self, hoja_id: UUID, hoja_in: HojaDeVidaUpdate) -> HojaDeVidaInDBBase:
        hoja_db = await hoja_de_vida_crud.get(self.db, hoja_id)
        if not hoja_db:
            raise HTTPException(status_code=404, detail="Hoja de vida no encontrada")

        return await hoja_de_vida_crud.update(self.db, db_obj=hoja_db, obj_in=hoja_in)

    async def delete(self, hoja_id: UUID) -> None:
        hoja_db = await hoja_de_vida_crud.get(self.db, hoja_id)
        if not hoja_db:
            raise HTTPException(status_code=404, detail="Hoja de vida no encontrada")

        await hoja_de_vida_crud.remove(self.db, hoja_id)
