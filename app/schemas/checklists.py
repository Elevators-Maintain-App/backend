# app/schemas/checklists.py

from datetime import datetime, time
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel

class ChecklistBase(BaseModel):
    hora_entrada: Optional[time] = None
    hora_salida: Optional[time] = None
    lista_revisiones: Optional[Dict[str, Any]] = None
    observaciones: Optional[str] = None
    firma_tecnico: Optional[str] = None
    firma_cliente: Optional[str] = None
    orden_trabajo_id: UUID

class ChecklistCreate(ChecklistBase):
    pass

class ChecklistUpdate(BaseModel):
    hora_entrada: Optional[time] = None
    hora_salida: Optional[time] = None
    lista_revisiones: Optional[Dict[str, Any]] = None
    observaciones: Optional[str] = None
    firma_tecnico: Optional[str] = None
    firma_cliente: Optional[str] = None
    orden_trabajo_id: Optional[UUID] = None

class ChecklistInDBBase(ChecklistBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
