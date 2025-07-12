#app/schemas/dashboard/supervisor.py

from dataclasses import dataclass
from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import date

@dataclass
class SupervisorDashboard:
    ordenes_trabajo: int
    validadas: int
    pendientes: int

class OrdenResumenSupervisor(BaseModel):
    id: UUID
    cliente: str
    tecnico: str
    proyecto: str
    unidad: str
    descripcion: str
    observaciones: str
    estado: str
    fecha_programada: date
    prioridad: str
    tipo_orden: str

class DashboardSupervisorOut(BaseModel):
    ordenes_programadas: int
    ordenes_cerradas: int
    ordenes_por_validar: int
    ordenes_pendientes: int
    ordenes_en_ejecucion: int
    ordenes_atrasadas: int
    cumplimiento_decimal: float
    cumplimiento_label: str
    cumplimiento_str: str
    ordenes: List[OrdenResumenSupervisor]