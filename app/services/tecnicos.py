# app/services/tecnicos.py

from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.tecnicos import tecnico_crud
from app.db.repositories.zonas_geograficas import zona_geografica_crud
from app.db.repositories.ordenes_de_trabajo import orden_de_trabajo_crud
from app.db.repositories.checklists import checklist_crud
from app.schemas.tecnicos import TecnicoCreate, TecnicoUpdate, TecnicoInDBBase
from app.schemas.ordenes_de_trabajo import OrdenDeTrabajoInDBBase
from app.schemas.checklists import ChecklistInDBBase

class TecnicoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[TecnicoInDBBase]:
        return await tecnico_crud.get_multi(self.db)

    async def get_by_id(self, tecnico_id: UUID) -> TecnicoInDBBase:
        tecnico = await tecnico_crud.get(self.db, tecnico_id)
        if not tecnico:
            raise HTTPException(status_code=404, detail="Técnico no encontrado")
        return tecnico

    async def create(self, tecnico_in: TecnicoCreate) -> TecnicoInDBBase:
        # Validar existencia de zona geográfica
        zona = await zona_geografica_crud.get(self.db, tecnico_in.zona_geografica_id)
        if not zona:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La zona geográfica especificada no existe."
            )

        # Validar unicidad de nombre
        existing_nombre = await tecnico_crud.get_by_field(self.db, field="nombre", value=tecnico_in.nombre)
        if existing_nombre:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un técnico con este nombre."
            )

        # Validar unicidad de email
        existing_email = await tecnico_crud.get_by_field(self.db, field="email", value=tecnico_in.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un técnico con este correo electrónico."
            )

        return await tecnico_crud.create(self.db, obj_in=tecnico_in)

    async def update(self, tecnico_id: UUID, tecnico_in: TecnicoUpdate) -> TecnicoInDBBase:
        tecnico_db = await tecnico_crud.get(self.db, tecnico_id)
        if not tecnico_db:
            raise HTTPException(status_code=404, detail="Técnico no encontrado")

        return await tecnico_crud.update(self.db, db_obj=tecnico_db, obj_in=tecnico_in)

    async def delete(self, tecnico_id: UUID) -> None:
        tecnico_db = await tecnico_crud.get(self.db, tecnico_id)
        if not tecnico_db:
            raise HTTPException(status_code=404, detail="Técnico no encontrado")

        await tecnico_crud.remove(self.db, tecnico_id)

    # Métodos especiales:

    async def get_ordenes_trabajo(self, tecnico_id: UUID) -> List[OrdenDeTrabajoInDBBase]:
        ordenes = await orden_de_trabajo_crud.get_multi_by_field(self.db, field="tecnico_id", value=tecnico_id)
        return ordenes

    async def get_checklists(self, tecnico_id: UUID) -> List[ChecklistInDBBase]:
        checklists = await checklist_crud.get_multi_by_field(self.db, field="tecnico_id", value=tecnico_id)
        return checklists