from typing import Optional
from pydantic import BaseModel
from uuid import UUID

class NivelTecnicoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    compania_id: Optional[UUID] = None

class NivelTecnicoCreate(NivelTecnicoBase):
    pass

class NivelTecnicoUpdate(NivelTecnicoBase):
    nombre: Optional[str] = None