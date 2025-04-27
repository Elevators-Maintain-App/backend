# app/services/clientes.py

from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.clientes import cliente_crud
from app.db.repositories.proyectos import proyecto_crud
from app.db.repositories.unidades import unidad_crud
from app.db.repositories.ordenes_de_trabajo import orden_de_trabajo_crud

from app.schemas.clientes import ClienteCreate, ClienteUpdate, ClienteInDBBase
from app.schemas.proyectos import ProyectoInDBBase
from app.schemas.unidades import UnidadInDBBase
from app.schemas.ordenes_de_trabajo import OrdenDeTrabajoInDBBase

class ClienteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[ClienteInDBBase]:
        return await cliente_crud.get_multi(self.db)

    async def get_by_id(self, cliente_id: UUID) -> ClienteInDBBase:
        cliente = await cliente_crud.get(self.db, cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        return cliente

    async def create(self, cliente_in: ClienteCreate) -> ClienteInDBBase:
        # Aquí debería estar tu validación de unicidad, ya implementada antes
        return await cliente_crud.create(self.db, obj_in=cliente_in)

    async def update(self, cliente_id: UUID, cliente_in: ClienteUpdate) -> ClienteInDBBase:
        cliente_db = await cliente_crud.get(self.db, cliente_id)
        if not cliente_db:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        return await cliente_crud.update(self.db, db_obj=cliente_db, obj_in=cliente_in)

    async def delete(self, cliente_id: UUID) -> None:
        cliente_db = await cliente_crud.get(self.db, cliente_id)
        if not cliente_db:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        await cliente_crud.remove(self.db, cliente_id)

    # Métodos especiales:

    async def get_proyectos(self, cliente_id: UUID) -> List[ProyectoInDBBase]:
        proyectos = await proyecto_crud.get_multi_by_field(self.db, field="cliente_id", value=cliente_id)
        return proyectos

    async def get_unidades(self, cliente_id: UUID) -> List[UnidadInDBBase]:
        proyectos = await proyecto_crud.get_multi_by_field(self.db, field="cliente_id", value=cliente_id)
        if not proyectos:
            return []
        
        proyecto_ids = [proyecto.id for proyecto in proyectos]
        unidades = await unidad_crud.get_multi_by_fields(self.db, field="proyecto_id", values=proyecto_ids)
        return unidades

    async def get_ordenes_trabajo(self, cliente_id: UUID) -> List[OrdenDeTrabajoInDBBase]:
        proyectos = await proyecto_crud.get_multi_by_field(self.db, field="cliente_id", value=cliente_id)
        if not proyectos:
            return []
        
        proyecto_ids = [proyecto.id for proyecto in proyectos]
        unidades = await unidad_crud.get_multi_by_fields(self.db, field="proyecto_id", values=proyecto_ids)
        if not unidades:
            return []
        
        unidad_ids = [unidad.id for unidad in unidades]
        ordenes = await orden_de_trabajo_crud.get_multi_by_fields(self.db, field="unidad_id", values=unidad_ids)
        return ordenes
