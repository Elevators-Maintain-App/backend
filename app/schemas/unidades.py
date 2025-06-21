# app/schemas/unidades.py

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class UnidadBase(BaseModel):
    nombre: str
    kpi_funcionamiento: Optional[str] = None
    proyecto_id: UUID
    tipo_unidad_id: int

class UnidadCreate(UnidadBase):
    pass  # company_id viene del token

class UnidadCreateInDB(UnidadCreate):
    company_id: UUID
    cliente_id: str

class UnidadUpdate(BaseModel):
    nombre: Optional[str] = None
    kpi_funcionamiento: Optional[str] = None
    proyecto_id: Optional[UUID] = None
    tipo_unidad_id: Optional[int] = None

class UnidadInDBBase(UnidadBase):
    nombre: str
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UnidadListOut(BaseModel):
    id: UUID
    nombre: str
    kpi_funcionamiento: Optional[str]
    proyecto: str
    cliente: str
    tipo_unidad_id: int
    tipo_unidad: str
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True