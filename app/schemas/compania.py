from pydantic import BaseModel, EmailStr, Field, UUID4
from typing import Optional, List
from datetime import datetime

# Base Compania Schema
class CompaniaBase(BaseModel):
    documento: str = Field(..., description="Documento de identificación de la compañía")
    tipo_documento_id: int = Field(..., description="ID del tipo de documento que usa esta compañía")
    nombre: Optional[str] = Field(None, description="Nombre de la compañía")
    email: Optional[str] = Field(None, description="Correo electrónico de la compañía")
    telefono: Optional[str] = Field(None, description="Teléfono de la compañía")

# Schema for creating a new company
class CompaniaCreate(CompaniaBase):
    pass

# Schema for updating a company
class CompaniaUpdate(BaseModel):
    documento: Optional[str] = Field(None, description="Documento de identificación de la compañía")
    tipo_documento_id: Optional[int] = Field(None, description="ID del tipo de documento")
    nombre: Optional[str] = Field(None, description="Nombre de la compañía")
    email: Optional[str] = Field(None, description="Correo electrónico de la compañía")
    telefono: Optional[str] = Field(None, description="Teléfono de la compañía")

# Schema for reading a company
class Compania(CompaniaBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

# Schema for company with document type information
class CompaniaWithDocumentType(Compania):
    document_type_in_use: Optional["TipoDocumentoBasic"] = None

    model_config = {
        "from_attributes": True
    }

# Schema for company with owned document types
class CompaniaWithOwnedTypes(Compania):
    owned_document_types: List["TipoDocumentoBasic"] = []

    model_config = {
        "from_attributes": True
    }

# Schema for company with all document type relationships
class CompaniaWithAllDocumentTypes(Compania):
    document_type_in_use: Optional["TipoDocumentoBasic"] = None
    owned_document_types: List["TipoDocumentoBasic"] = []

    model_config = {
        "from_attributes": True
    }

# Basic document type schema to avoid circular imports
class TipoDocumentoBasic(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    is_system_wide: bool

    model_config = {
        "from_attributes": True
    }

# Update forward references
CompaniaWithDocumentType.model_rebuild()
CompaniaWithOwnedTypes.model_rebuild()
CompaniaWithAllDocumentTypes.model_rebuild() 