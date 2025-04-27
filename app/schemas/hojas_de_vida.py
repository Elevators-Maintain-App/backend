# app/schemas/hojas_de_vida.py

from datetime import datetime, date
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel

class HojaDeVidaBase(BaseModel):
    historial_trabajos: Optional[Dict[str, Any]] = None
    lista_trabajos_programados: Optional[Dict[str, Any]] = None
    fecha_proximo_mantenimiento: Optional[date] = None
    unidad_id: UUID

class HojaDeVidaCreate(HojaDeVidaBase):
    pass

class HojaDeVidaUpdate(BaseModel):
    historial_trabajos: Optional[Dict[str, Any]] = None
    lista_trabajos_programados: Optional[Dict[str, Any]] = None
    fecha_proximo_mantenimiento: Optional[date] = None
    unidad_id: Optional[UUID] = None

class HojaDeVidaInDBBase(HojaDeVidaBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
