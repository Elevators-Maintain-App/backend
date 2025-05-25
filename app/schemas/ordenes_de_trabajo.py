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
    tecnico_id: str   
    supervisor_id: Optional[str]

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
    referencia: str
    supervisor_id: str
    company_id: UUID
    tecnico_id:    str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrdenDeTrabajoCountOut(BaseModel):
    count: int

class OrdenTrabajoListOut(BaseModel):
    id: UUID
    referencia: str               
    descripcion: Optional[str]
    fecha: Optional[date]
    tipo_orden: str
    estado: str
    prioridad: str
    supervisor_id: str
    supervisor_nombre: str
    tecnico_id: str
    tecnico_nombre: str
    unidad_id: UUID
    unidad_nombre: str
    cliente_nombre: str
    compania_nombre: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Para el detalle completo
class OrdenTrabajoDetailOut(BaseModel):
    id: UUID
    referencia: str
    fecha: Optional[date]
    descripcion: Optional[str]
    observaciones: Optional[str]
    valor: Optional[Decimal]
    tipo_orden: str
    estado: str
    prioridad: str
    unidad_id: UUID
    supervisor_id: str
    tecnico_id: str
    cliente: str
    compania: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Para el listado admin
class OrdenDeTrabajoSummaryOut(BaseModel):
    id: UUID
    referencia: str
    fecha: Optional[date]
    supervisor_id: str
    tecnico_id: str
    unidad_id: UUID
    company_id: UUID
    tipo_orden_id: int
    estado_id: int
    prioridad_id: int

    class Config:
        from_attributes = True

# Para resumen rápido de supervisor
class OrdenDeTrabajoSummarySupervisorOut(BaseModel):
    id: UUID
    proyecto_nombre: str
    unidad_nombre: str
    fecha: Optional[date]
    estado: str

# Para progreso semanal
class OrdenDeTrabajoWeeklyComplianceOut(BaseModel):
    text: str   # "33%"
    value: float  # 0.33
    detail: str   # "1 de 3 Validadas"