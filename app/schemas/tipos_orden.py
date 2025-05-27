# app/schemas/tipos_orden.py

from datetime import datetime
from pydantic import BaseModel

class TipoOrdenBase(BaseModel):
    nombre: str

class TipoOrdenCreate(TipoOrdenBase):
    pass

class TipoOrdenUpdate(BaseModel):
    nombre: str

class TipoOrdenInDBBase(TipoOrdenBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
