# app/schemas/tecnicos.py

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class TecnicoBase(BaseModel):
    nombre: Optional[str] = None
    nivel: Optional[str] = None
    zona_geografica_id: Optional[UUID] = None

class TecnicoCreate(TecnicoBase):
    pass

class TecnicoUpdate(BaseModel):
    nombre: Optional[str] = None
    nivel: Optional[str] = None
    zona_geografica_id: Optional[UUID] = None

class TecnicoInDBBase(TecnicoBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
