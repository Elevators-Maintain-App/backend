# app/schemas/tipos_documento.py

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

class TipoDocumentoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    is_system_wide: bool = False

class TipoDocumentoCreate(TipoDocumentoBase):
    owner_compania_id: Optional[UUID] = Field(None, alias="compania_id")

class TipoDocumentoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    is_system_wide: Optional[bool] = None

class TipoDocumentoInDBBase(TipoDocumentoBase):
    id: int
    owner_compania_id: Optional[UUID] = Field(None, alias="compania_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Alias for backward compatibility
TipoDocumento = TipoDocumentoInDBBase

# Optional: Schema with relationships (if you need them)
class TipoDocumentoWithRelations(TipoDocumentoInDBBase):
    owner_compania: Optional["CompaniaBasic"] = None
    companies_using_this_type: List["CompaniaBasic"] = []

    class Config:
        from_attributes = True

# Basic company schema to avoid circular imports
class CompaniaBasic(BaseModel):
    id: UUID
    nombre: Optional[str]
    documento: str

    class Config:
        from_attributes = True

# Update forward references
TipoDocumentoWithRelations.model_rebuild()
