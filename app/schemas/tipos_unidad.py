# app/schemas/tipos_unidad.py

from datetime import datetime
from pydantic import BaseModel

class TipoUnidadBase(BaseModel):
    nombre: str

class TipoUnidadCreate(TipoUnidadBase):
    pass

class TipoUnidadUpdate(BaseModel):
    nombre: str

class TipoUnidadInDBBase(TipoUnidadBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
