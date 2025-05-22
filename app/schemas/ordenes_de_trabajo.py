# app/schemas/ordenes_de_trabajo.py

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class OrdenDeTrabajoBase(BaseModel):
    descripcion: Optional[str]
    observaciones: Optional[str]
    valor: Optional[Decimal]
    fecha: Optional[date]
    tipo_orden_id: int
    estado_id: int
    prioridad_id: int
    unidad_id: UUID

class OrdenDeTrabajoCreate(OrdenDeTrabajoBase):
    tecnico_id: str   # UID de Firestore del técnico

class OrdenDeTrabajoUpdate(BaseModel):
    descripcion: Optional[str]
    observaciones: Optional[str]
    valor: Optional[Decimal]
    fecha: Optional[date]
    tipo_orden_id: Optional[int]
    estado_id: Optional[int]
    prioridad_id: Optional[int]
    unidad_id: Optional[UUID]
    tecnico_id: Optional[str]

class OrdenDeTrabajoInDBBase(OrdenDeTrabajoBase):
    id: UUID
    supervisor_id: str
    company_id: UUID
    tecnico_id:    str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
