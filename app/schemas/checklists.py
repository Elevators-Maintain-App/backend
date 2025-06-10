from datetime import datetime, time
from typing import Optional, Any, Dict, List
from uuid import UUID
from pydantic import BaseModel, Field

# ► Plantilla y pasos de plantilla

class ChecklistItemTemplateOut(BaseModel):
    step_number: int
    titulo: str
    instrucciones: str
    evidencia_schema: Dict[str, Any]

    class Config:
        from_attributes = True

class ChecklistTemplateOut(BaseModel):
    id: UUID
    nombre: str
    tipo_orden_id: int
    tipo_unidad_id: int
    pasos: List[ChecklistItemTemplateOut]
    total_steps: int
    step_numbers: List[int]
    pasos_ids: List[UUID]    
    current_step: int 

    class Config:
        from_attributes = True

# ► Ejecución de checklist y sus items

class ChecklistItemOut(BaseModel):
    step_number: int
    titulo: str
    instrucciones: str      
    evidencia_schema: Dict[str, Any]
    is_completed: bool            
    evidencia_data: Dict[str, Any]
    comentario: Optional[str] 
    confirmed_at: Optional[datetime]

    class Config:
        from_attributes = True

class ChecklistOut(BaseModel):
    id: UUID
    orden_trabajo_id: UUID
    hora_entrada: Optional[time]
    hora_salida: Optional[time]
    observaciones: Optional[str]
    firma_tecnico: Optional[str]
    firma_cliente: Optional[str]
    check_metadata: Dict[str, Any]
    items: List[ChecklistItemOut]

    # datos para el stepper
    total_steps: int
    step_numbers: List[int]
    current_step: int

    class Config:
        from_attributes = True

# ► Creación y actualización de items

class ChecklistCreate(BaseModel):
    orden_trabajo_id: UUID

class ChecklistItemUpdate(BaseModel):
    evidencia_data: Optional[Dict[str, Any]] = None
    comentario:   Optional[str] = None
    confirm: Optional[bool] = False


# Paso de plantilla entrante
class ChecklistItemTemplateCreate(BaseModel):
    step_number: int = Field(..., gt=0)
    titulo: str
    instrucciones: str
    evidencia_schema: Dict[str, Any]

# Plantilla entrante
class ChecklistTemplateCreate(BaseModel):
    nombre: str
    tipo_orden_id: int
    tipo_unidad_id: int
    pasos: List[ChecklistItemTemplateCreate]

