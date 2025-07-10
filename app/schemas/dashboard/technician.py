# app/schemas/dashboard/technician.py

from dataclasses import dataclass
from pydantic import BaseModel
from typing import List, Literal, Optional
from datetime import date
import uuid 
from uuid import UUID

@dataclass
class TechnicianDashboard:
    ordenes_trabajo: int
    validadas: int
    pendientes: int

class OrdenEnCursoOut(BaseModel):
    id: UUID
    cliente: Optional[str]
    tecnico: Optional[str]
    proyecto: str
    unidad: str
    descripcion: str
    observaciones: str
    estado: Literal["Pendiente", "En ejecución", "En Pausa", "En Validación", "Cerrada"]
    fecha_programada: date
    prioridad: str
    tipo_orden: str


class DashboardTecnicoOut(BaseModel):
    ordenes_programadas: int
    ordenes_completadas: int
    ordenes_pendientes: int
    cumplimiento_decimal: float
    cumplimiento_label: str
    ordenes_en_curso: List[OrdenEnCursoOut]
    cumplimiento_str: str