# app/schemas/ordenes_de_trabajo.py

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class OrdenDeTrabajoBase(BaseModel):
    descripcion: Optional[str] = None
    observaciones: Optional[str] = None
    valor: Optional[Decimal] = None
    fecha: Optional[date] = None
    tipo_orden_id: int
    estado_id: int
    prioridad_id: int
    unidad_id: UUID
    supervisor_id: UUID
    tecnico_id: UUID

class OrdenDeTrabajoCreate(OrdenDeTrabajoBase):
    pass

class OrdenDeTrabajoUpdate(BaseModel):
    descripcion: Optional[str] = None
    observaciones: Optional[str] = None
    valor: Optional[Decimal] = None
    fecha: Optional[date] = None
    tipo_orden_id: Optional[int] = None
    estado_id: Optional[int] = None
    prioridad_id: Optional[int] = None
    unidad_id: Optional[UUID] = None
    supervisor_id: Optional[UUID] = None
    tecnico_id: Optional[UUID] = None

class OrdenDeTrabajoInDBBase(OrdenDeTrabajoBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
