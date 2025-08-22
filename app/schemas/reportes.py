from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class UrlReporteOut(BaseModel):
    url: str

class ReportePrerevisionOut(BaseModel):
    url: str
    proyecto: str
    unidad: str
    estado: str
    fecha: datetime