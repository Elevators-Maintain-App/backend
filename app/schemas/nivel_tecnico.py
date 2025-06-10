from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class NivelTecnicoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class NivelTecnico(NivelTecnicoBase):
    id: UUID
    compania_id: UUID
    created_at: datetime
    updated_at: datetime

class NivelTecnicoCreate(NivelTecnicoBase):
    compania_id: UUID

class NivelTecnicoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None