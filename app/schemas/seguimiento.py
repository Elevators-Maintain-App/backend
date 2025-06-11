# app/schemas/seguimiento.py
from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class EventoOrden(str, Enum):
    """Eventos que se pueden registrar en la tabla de seguimiento."""
    INICIO = "INICIO"
    PAUSA = "PAUSA"
    REANUDACION = "REANUDACION"
    FIN = "FIN"
    PASO_COMPLETADO = "PASO_COMPLETADO"


class SeguimientoCreate(BaseModel):
    """
    Payload que envía el frontend para registrar un nuevo evento
    de seguimiento (ubicación + timestamp).
    """
    evento: EventoOrden = Field(..., description="Tipo de evento a registrar")
    lat: float | None = Field(None, description="Latitud GPS")
    lon: float | None = Field(None, description="Longitud GPS")
    timestamp: datetime | None = Field(
        None,
        description="Momento del evento; si se omite, el servidor usará la hora actual (UTC)"
    )
    checklist_item_id: UUID | None = Field(
        None,
        description="UUID del ítem de checklist (solo para PASO_COMPLETADO)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "evento": "INICIO",
                    "lat": 8.9833,
                    "lon": -79.5167,
                    "timestamp": "2025-06-11T13:05:00Z"
                },
                {
                    "evento": "PASO_COMPLETADO",
                    "lat": 8.9833,
                    "lon": -79.5167,
                    "checklist_item_id": "d4448f9e-ff6b-4203-8fb7-0c9f8a5bb2da"
                }
            ]
        }
    }
