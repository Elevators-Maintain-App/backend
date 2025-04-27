# app/services/proyectos.py

from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.proyectos import proyecto_crud
from app.db.repositories.clientes import cliente_crud
from app.db.repositories.zonas_geograficas import zona_geografica_crud
from app.schemas.proyectos import ProyectoCreate, ProyectoUpdate, ProyectoInDBBase

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

    async def create(self, proyecto_in: ProyectoCreate) -> ProyectoInDBBase:
        # Validar que el cliente exista
        cliente = await cliente_crud.get(self.db, proyecto_in.cliente_id)
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El cliente especificado no existe."
            )

        # Validar que la zona geográfica exista
        zona = await zona_geografica_crud.get(self.db, proyecto_in.zona_geografica_id)
        if not zona:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La zona geográfica especificada no existe."
            )

        # Validar unicidad de nombre de proyecto
        existing_nombre = await proyecto_crud.get_by_field(self.db, field="nombre", value=proyecto_in.nombre)
        if existing_nombre:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un proyecto con este nombre."
            )

        return await proyecto_crud.create(self.db, obj_in=proyecto_in)

    async def update(self, proyecto_id: UUID, proyecto_in: ProyectoUpdate) -> ProyectoInDBBase:
        proyecto_db = await proyecto_crud.get(self.db, proyecto_id)
        if not proyecto_db:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")

        return await proyecto_crud.update(self.db, db_obj=proyecto_db, obj_in=proyecto_in)

    async def delete(self, proyecto_id: UUID) -> None:
        proyecto_db = await proyecto_crud.get(self.db, proyecto_id)
        if not proyecto_db:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")

        await proyecto_crud.remove(self.db, proyecto_id)
