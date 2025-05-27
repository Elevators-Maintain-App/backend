# app/schemas/clientes.py

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class ClienteBase(BaseModel):
    documento: str
    tipo_documento_id: int
    nombre: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(BaseModel):
    documento: Optional[str] = None
    tipo_documento_id: Optional[int] = None
    nombre: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None

class ClienteInDBBase(ClienteBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
