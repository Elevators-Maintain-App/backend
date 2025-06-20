# app/schemas/proyectos.py

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from enum import Enum

class ProyectoEstado(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"

class ProyectoBase(BaseModel):
    nombre: str
    direccion: Optional[str] = None
    estado: Optional[ProyectoEstado] = None
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

class ProyectoCreateInDB(ProyectoCreate):
    company_id: UUID

class ProyectoDetailOut(BaseModel):
    id: UUID
    nombre: str
    direccion: str | None
    zona_geografica: str | None
    cliente: str
    compania: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProyectoListOut(BaseModel):
    id: UUID
    nombre: str
    direccion: str | None
    zona_geografica: str | None
    cliente: str
    compania: str

    class Config:
        from_attributes = True