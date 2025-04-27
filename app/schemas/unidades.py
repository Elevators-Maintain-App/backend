# app/schemas/unidades.py

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class UnidadBase(BaseModel):
    kpi_funcionamiento: Optional[str] = None
    proyecto_id: UUID
    tipo_unidad_id: int

class UnidadCreate(UnidadBase):
    pass

class UnidadUpdate(BaseModel):
    kpi_funcionamiento: Optional[str] = None
    proyecto_id: Optional[UUID] = None
    tipo_unidad_id: Optional[int] = None

class UnidadInDBBase(UnidadBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
