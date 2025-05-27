# app/schemas/estados_orden.py

from datetime import datetime
from pydantic import BaseModel

class EstadoOrdenBase(BaseModel):
    nombre: str

class EstadoOrdenCreate(EstadoOrdenBase):
    pass

class EstadoOrdenUpdate(BaseModel):
    nombre: str

class EstadoOrdenInDBBase(EstadoOrdenBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
