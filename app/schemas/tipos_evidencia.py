# app/schemas/tipos_evidencia.py

from datetime import datetime
from pydantic import BaseModel

class TipoEvidenciaBase(BaseModel):
    nombre: str

class TipoEvidenciaCreate(TipoEvidenciaBase):
    pass

class TipoEvidenciaUpdate(BaseModel):
    nombre: str

class TipoEvidenciaInDBBase(TipoEvidenciaBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
