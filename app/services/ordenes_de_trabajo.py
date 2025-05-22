# app/services/ordenes_de_trabajo.py

from typing import List
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.repositories.ordenes_de_trabajo import orden_de_trabajo_crud
from app.db.repositories.unidades import unidad_crud
from app.db.repositories.tipos_orden import tipo_orden_crud
from app.db.repositories.estados_orden import estado_orden_crud
from app.db.repositories.prioridades import prioridad_crud
from app.db.repositories.usuarios import usuario_crud
from app.schemas.ordenes_de_trabajo import OrdenDeTrabajoCreate, OrdenDeTrabajoUpdate, OrdenDeTrabajoInDBBase
from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo

class OrdenDeTrabajoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[OrdenDeTrabajoInDBBase]:
        return await orden_de_trabajo_crud.get_multi(self.db)

    async def get_by_id(self, orden_id: UUID) -> OrdenDeTrabajoInDBBase:
        orden = await orden_de_trabajo_crud.get(self.db, orden_id)
        if not orden:
            raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
        return orden

    async def create(self, orden_in: OrdenDeTrabajoCreate) -> OrdenDeTrabajoInDBBase:
        # Validar existencia de unidad
        unidad = await unidad_crud.get(self.db, orden_in.unidad_id)
        if not unidad:
            raise HTTPException(status_code=400, detail="La unidad especificada no existe.")

        # Validar existencia de técnico
        tecnico = await usuario_crud.get(self.db, orden_in.tecnico_id)
        if not tecnico or tecnico.role != "tecnico":
            raise HTTPException(status_code=400, detail="El técnico especificado no existe.")

        # Validar existencia de supervisor
        supervisor = await usuario_crud.get(self.db, orden_in.supervisor_id)
        if not supervisor or supervisor.role != "supervisor":
            raise HTTPException(status_code=400, detail="El supervisor especificado no existe.")
        
        # Validar existencia de tipo de orden
        tipo_orden = await tipo_orden_crud.get(self.db, orden_in.tipo_orden_id)
        if not tipo_orden:
            raise HTTPException(status_code=400, detail="El tipo de orden especificado no existe.")

        # Validar existencia de estado
        estado = await estado_orden_crud.get(self.db, orden_in.estado_id)
        if not estado:
            raise HTTPException(status_code=400, detail="El estado especificado no existe.")

        # Validar existencia de prioridad
        prioridad = await prioridad_crud.get(self.db, orden_in.prioridad_id)
        if not prioridad:
            raise HTTPException(status_code=400, detail="La prioridad especificada no existe.")

        return await orden_de_trabajo_crud.create(self.db, obj_in=orden_in)

    async def update(self, orden_id: UUID, orden_in: OrdenDeTrabajoUpdate) -> OrdenDeTrabajoInDBBase:
        orden_db = await orden_de_trabajo_crud.get(self.db, orden_id)
        if not orden_db:
            raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")

        return await orden_de_trabajo_crud.update(self.db, db_obj=orden_db, obj_in=orden_in)

    async def delete(self, orden_id: UUID) -> None:
        orden_db = await orden_de_trabajo_crud.get(self.db, orden_id)
        if not orden_db:
            raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")

        await orden_de_trabajo_crud.remove(self.db, orden_id)

    async def listar_por_supervisor(self, supervisor_uid: str):
        q = select(OrdenDeTrabajo).where(OrdenDeTrabajo.supervisor_id == supervisor_uid)
        res = await self.db.execute(q.order_by(OrdenDeTrabajo.fecha))
        return res.scalars().all()

    async def crear_para_supervisor(self, orden_in, supervisor_uid: str, company_id: str):
        nueva = OrdenDeTrabajo(
            id=uuid4(),
            **orden_in.dict(),
            company_id=company_id,
            supervisor_id=supervisor_uid
        )
        self.db.add(nueva)
        await self.db.commit()
        await self.db.refresh(nueva)
        return nueva