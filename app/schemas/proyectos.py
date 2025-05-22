# app/schemas/proyectos.py

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class ProyectoBase(BaseModel):
    nombre: str
    direccion: Optional[str] = None
    zona_geografica_id: Optional[UUID] = None
    cliente_id: str

class ProyectoCreate(ProyectoBase):
    pass

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    direccion: Optional[str] = None
    zona_geografica_id: Optional[UUID] = None
    cliente_id: str | None

class ProyectoInDBBase(ProyectoBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CountOut(BaseModel):
    count: int

class ProyectoCreateAdmin(ProyectoBase):
    company_id: UUID