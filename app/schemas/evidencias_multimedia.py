# app/schemas/evidencias_multimedia.py

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class EvidenciaMultimediaBase(BaseModel):
    url: Optional[str] = None
    ubicacion_gps: Optional[str] = None
    fecha_hora: Optional[datetime] = None
    tipo_evidencia_id: int
    orden_trabajo_id: UUID

class EvidenciaMultimediaCreate(EvidenciaMultimediaBase):
    pass

class EvidenciaMultimediaUpdate(BaseModel):
    url: Optional[str] = None
    ubicacion_gps: Optional[str] = None
    fecha_hora: Optional[datetime] = None
    tipo_evidencia_id: Optional[int] = None
    orden_trabajo_id: Optional[UUID] = None

class EvidenciaMultimediaInDBBase(EvidenciaMultimediaBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
