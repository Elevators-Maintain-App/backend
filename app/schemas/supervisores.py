# app/schemas/supervisores.py

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class SupervisorBase(BaseModel):
    nombre: Optional[str] = None

class SupervisorCreate(SupervisorBase):
    pass

class SupervisorUpdate(BaseModel):
    nombre: Optional[str] = None

class SupervisorInDBBase(SupervisorBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
