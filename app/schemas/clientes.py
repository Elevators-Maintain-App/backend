# app/schemas/clientes.py

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class ClienteBase(BaseModel):
    documento: str
    tipo_documento_id: int
    nombre: str
    email: str
    telefono: str
    pais_id: int
    ciudad: str
    direccion: str
    logo: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(BaseModel):
    documento: Optional[str] = None
    tipo_documento_id: Optional[int] = None
    nombre: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    pais_id: Optional[int] = None
    ciudad: Optional[str] = None
    direccion: Optional[str] = None
    logo: Optional[str] = None

class ClienteSchema(ClienteBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
