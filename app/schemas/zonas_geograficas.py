# app/schemas/zonas_geograficas.py

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class ZonaGeograficaBase(BaseModel):
    nombre: Optional[str] = None

class ZonaGeograficaCreate(ZonaGeograficaBase):
    pass

class ZonaGeograficaUpdate(BaseModel):
    nombre: Optional[str] = None

class ZonaGeograficaInDBBase(ZonaGeograficaBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
