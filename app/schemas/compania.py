from pydantic import BaseModel, EmailStr, Field, UUID4
from typing import Optional
from datetime import datetime

# Base Compania Schema
class CompaniaBase(BaseModel):
    documento: str = Field(..., description="Documento de identificación de la compañía")
    tipo_documento_id: int = Field(..., description="ID del tipo de documento")
    nombre: Optional[str] = Field(None, description="Nombre de la compañía")
    email: Optional[str] = Field(None, description="Correo electrónico de la compañía")
    telefono: Optional[str] = Field(None, description="Teléfono de la compañía")

# Schema for creating a company
class CompaniaCreate(CompaniaBase):
    pass

# Schema for updating a company
class CompaniaUpdate(BaseModel):
    documento: Optional[str] = Field(None, description="Documento de identificación de la compañía")
    tipo_documento_id: Optional[int] = Field(None, description="ID del tipo de documento")
    nombre: Optional[str] = Field(None, description="Nombre de la compañía")
    email: Optional[str] = Field(None, description="Correo electrónico de la compañía")
    telefono: Optional[str] = Field(None, description="Teléfono de la compañía")

# Schema for company in response
class Compania(CompaniaBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

# Schema for company with related entities
class CompaniaWithRelations(Compania):
    tipo_documento: Optional["TipoDocumento"] = None

    model_config = {
        "from_attributes": True
    }

# Forward references
from app.schemas.tipo_documento import TipoDocumento  # noqa: E402
CompaniaWithRelations.model_rebuild() 