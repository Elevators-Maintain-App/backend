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
    cliente_id: UUID

class ProyectoCreate(ProyectoBase):
    company_id: Optional[UUID] = None

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    direccion: Optional[str] = None
    zona_geografica_id: Optional[UUID] = None
    cliente_id: Optional[UUID] = None

class ProyectoInDBBase(ProyectoBase):
    id: UUID
    company_id: UUID
    cliente_nombre: Optional[str] = None
    company_nombre: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CountOut(BaseModel):
    count: int

class ProyectoCreateInDB(ProyectoCreate):
    ...

class ProyectoDetailOut(BaseModel):
    id: UUID
    nombre: str
    direccion: str | None
    zona_geografica_id: UUID | None
    cliente_id: UUID | None
    cliente_nombre: str | None
    company_id: UUID | None
    company_nombre: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProyectoListOut(BaseModel):
    id: str
    nombre: str
    direccion: str | None
    zona_geografica: str | None
    cliente_id: UUID | None
    cliente_nombre: str | None
    company_id: str | None
    company_nombre: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProyectoOut(BaseModel):
    id: UUID
    nombre: str
    direccion: str | None = None
    estado: Optional[ProyectoEstado] = None
    zona_geografica_id: Optional[UUID] = None
    cliente_id: Optional[UUID] = None
    cliente_nombre: Optional[str] = None
    company_id: UUID
    company_nombre: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True