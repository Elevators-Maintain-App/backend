# app/schemas/supervisores.py

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel
from decimal import Decimal

class SupervisorBase(BaseModel):
    nombre: Optional[str] = None

class SupervisorCreate(SupervisorBase):
    pass

class SupervisorUpdate(BaseModel):
    nombre: Optional[str] = None

class SupervisorInDBBase(SupervisorBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Nuevo esquema: OrdenDashboardOut
class OrdenDashboardOut(BaseModel):
    id_orden: UUID
    proyecto_nombre: Optional[str]
    tecnico_nombre: Optional[str]
    tecnico_nivel: Optional[str]
    fecha_creacion: datetime
    estado_orden: Optional[str]
    descripcion: Optional[str]
    observaciones: Optional[str]
    valor: Optional[Decimal]

# Nuevo esquema: DashboardSupervisorOut
class DashboardSupervisorOut(BaseModel):
    ordenes_totales_mes: int
    ordenes_pendientes: int
    ordenes_finalizadas: int
    ordenes_en_progreso: int
    ordenes_recientes: List[OrdenDashboardOut]
