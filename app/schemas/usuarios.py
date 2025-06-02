# app/schemas/usuarios.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UsuarioBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str  # "tecnico", "supervisor", "admin", etc.
    nivel: Optional[str] = None
    zona_geografica_id: Optional[str] = None
    is_active: Optional[bool] = True

# Para creación desde el frontend o sincronización con Firebase
class UsuarioCreate(UsuarioBase):
    uid: str  # Firebase UID obligatorio

# Para actualizaciones parciales desde el backend
class UsuarioUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    nivel: Optional[str] = None
    zona_geografica_id: Optional[str] = None
    is_active: Optional[bool] = None

# Para respuestas generales
class UsuarioOut(UsuarioBase):
    uid: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UsuarioInDBBase(UsuarioOut):
    class Config:
        from_attributes = True

class UserOut(BaseModel):
    uid: str
    email: Optional[str]
    display_name: Optional[str]
    company_id: Optional[str]
    role: Optional[str]
    photo_url: Optional[str]
    company_name: Optional[str]

class CountOut(BaseModel):
    count: int
