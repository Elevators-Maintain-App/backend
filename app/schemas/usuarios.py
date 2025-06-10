# app/schemas/usuarios.py

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.db.models.usuarios import Rol

class UsuarioBase(BaseModel):
    company_id: UUID
    display_name: str
    document_id: str
    document_type_id: int
    email: str
    phone_number: str
    rol: Rol
    nivel: Optional[str] = None
    zona_geografica_id: Optional[UUID] = None
    photo_url: Optional[str] = None
    is_active: Optional[bool] = True


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
    is_active: Optional[bool] = None

# Para respuestas generales
class UsuarioOut(UsuarioBase):
    uid: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UsuarioListResponse(BaseModel):
    usuarios: List[UsuarioOut]
    total: int
    skip: int
    limit: int

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
