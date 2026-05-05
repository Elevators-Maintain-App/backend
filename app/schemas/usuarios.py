# app/schemas/usuarios.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.db.models.usuarios import Rol
from app.schemas.comunes import PaginacionResponse

class UsuarioBase(BaseModel):
    company_id: UUID = Field(..., description="ID de la empresa")
    display_name: str = Field(..., description="Nombre de usuario")
    document_id: str = Field(..., description="ID del documento")
    document_type_id: int = Field(..., description="ID del tipo de documento")
    email: str = Field(..., description="Correo electrónico")
    phone_number: str = Field(..., description="Número de teléfono")
    rol: Rol = Field(..., description="Rol del usuario")
    client_id: Optional[UUID] = Field(None, description="ID del cliente")
    nivel: Optional[str] = Field(None, description="Nivel del usuario")
    zona_geografica_id: Optional[UUID] = Field(None, description="ID de la zona geográfica")
    photo_url: Optional[str] = Field(None, description="URL de la foto del usuario")
    is_active: Optional[bool] = Field(None, description="Indica si el usuario está activo")


# Para creación desde el frontend o sincronización con Firebase
class UsuarioCreate(UsuarioBase): 
    uid: Optional[str] = None

class UsuarioUpdate(BaseModel):
    company_id: Optional[UUID] = None
    display_name: Optional[str] = None
    document_id: Optional[str] = None
    document_type_id: Optional[int] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    photo_url: Optional[str] = None
    rol: Optional[Rol] = None
    client_id: Optional[UUID] = None
    is_active: Optional[bool] = None

# Para respuestas generales
class UsuarioOut(UsuarioBase):
    id: UUID
    uid: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    company_name: Optional[str] = None
    document_type_name: Optional[str] = None

    class Config:
        from_attributes = True


class UsuarioInDBBase(UsuarioOut):
    class Config:
        from_attributes = True

class UserOut(BaseModel):
    uid: str
    email: Optional[str]
    display_name: Optional[str]
    company_id: Optional[UUID]
    role: Optional[Rol]
    photo_url: Optional[str]
    company_name: Optional[str]

class CountOut(BaseModel):
    count: int
