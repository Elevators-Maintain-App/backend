# app/schemas/tipos_documento.py

from datetime import datetime
from pydantic import BaseModel

class TipoDocumentoBase(BaseModel):
    nombre: str

class TipoDocumentoCreate(TipoDocumentoBase):
    pass

class TipoDocumentoUpdate(BaseModel):
    nombre: str

class TipoDocumentoInDBBase(TipoDocumentoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
