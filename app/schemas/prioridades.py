# app/schemas/prioridades.py

from datetime import datetime
from pydantic import BaseModel

class PrioridadBase(BaseModel):
    nombre: str

class PrioridadCreate(PrioridadBase):
    pass

class PrioridadUpdate(BaseModel):
    nombre: str

class PrioridadInDBBase(PrioridadBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
