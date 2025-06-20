# app/schemas/clientes.py

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class ClienteBase(BaseModel):
    documento: str = Field(..., description="Documento de identificación del cliente")
    tipo_documento_id: int = Field(..., description="ID del tipo de documento del cliente")
    compania_id: UUID = Field(..., description="ID de la compañía del cliente")
    nombre: str = Field(..., description="Nombre del cliente")
    email: str = Field(..., description="Correo electrónico del cliente")
    telefono: str = Field(..., description="Teléfono del cliente")
    pais_id: int = Field(..., description="ID del país del cliente")
    ciudad: str = Field(..., description="Ciudad del cliente")
    direccion: str = Field(..., description="Dirección del cliente")
    logo: Optional[str] = Field(None, description="Logo del cliente")

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(BaseModel):
    documento: Optional[str] = Field(None, description="Documento de identificación del cliente")
    tipo_documento_id: Optional[int] = Field(None, description="ID del tipo de documento del cliente")
    nombre: Optional[str] = Field(None, description="Nombre del cliente")
    email: Optional[str] = Field(None, description="Correo electrónico del cliente")
    telefono: Optional[str] = Field(None, description="Teléfono del cliente")
    pais_id: Optional[int] = Field(None, description="ID del país del cliente")
    ciudad: Optional[str] = Field(None, description="Ciudad del cliente")
    direccion: Optional[str] = Field(None, description="Dirección del cliente")
    logo: Optional[str] = Field(None, description="Logo del cliente")

class ClienteOut(ClienteBase):
    id: UUID
    nombre_pais: Optional[str] = None
    tipo_documento_nombre: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
