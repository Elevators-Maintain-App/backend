# app/services/checklists.py

from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.checklists import checklist_crud
from app.db.repositories.ordenes_de_trabajo import orden_de_trabajo_crud
from app.schemas.checklists import ChecklistCreate, ChecklistUpdate, ChecklistInDBBase

class ChecklistService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[ChecklistInDBBase]:
        return await checklist_crud.get_multi(self.db)

    async def get_by_id(self, checklist_id: UUID) -> ChecklistInDBBase:
        checklist = await checklist_crud.get(self.db, checklist_id)
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist no encontrado")
        return checklist

    async def create(self, checklist_in: ChecklistCreate) -> ChecklistInDBBase:
        # Validar existencia de orden de trabajo
        orden = await orden_de_trabajo_crud.get(self.db, checklist_in.orden_trabajo_id)
        if not orden:
            raise HTTPException(status_code=400, detail="La orden de trabajo especificada no existe.")

        return await checklist_crud.create(self.db, obj_in=checklist_in)

    async def update(self, checklist_id: UUID, checklist_in: ChecklistUpdate) -> ChecklistInDBBase:
        checklist_db = await checklist_crud.get(self.db, checklist_id)
        if not checklist_db:
            raise HTTPException(status_code=404, detail="Checklist no encontrado")

        return await checklist_crud.update(self.db, db_obj=checklist_db, obj_in=checklist_in)

    async def delete(self, checklist_id: UUID) -> None:
        checklist_db = await checklist_crud.get(self.db, checklist_id)
        if not checklist_db:
            raise HTTPException(status_code=404, detail="Checklist no encontrado")

        await checklist_crud.remove(self.db, checklist_id)
