#app/schemas/checklists_sync.py

from __future__ import annotations

from datetime import datetime, time
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ChecklistItemSync(BaseModel):
    step_number: int = Field(..., gt=0)
    is_completed: bool = False
    evidencia_data: Optional[Dict[str, Any]] = None
    comentario: Optional[str] = None


class ChecklistSyncPayload(BaseModel):
    id: Optional[UUID] = None
    orden_trabajo_id: UUID

    hora_entrada: Optional[Union[time, str]] = None
    hora_salida: Optional[Union[time, datetime, str]] = None

    observaciones: Optional[str] = None
    firma_tecnico: Optional[str] = None
    firma_cliente: Optional[str] = None
    check_metadata: Dict[str, Any] = Field(default_factory=dict)

    items: List[ChecklistItemSync]

    # opcional: único GPS “de inicio”
    lat: Optional[float] = None
    lon: Optional[float] = None

    @field_validator("hora_entrada", mode="before")
    @classmethod
    def _parse_hora_entrada(cls, v):
        if v is None or isinstance(v, time):
            return v
        if isinstance(v, str):
            for fmt in ("%H:%M:%S.%f", "%H:%M:%S", "%H:%M"):
                try:
                    return datetime.strptime(v, fmt).time()
                except ValueError:
                    pass
        raise ValueError("hora_entrada inválida")

    @field_validator("hora_salida", mode="before")
    @classmethod
    def _parse_hora_salida(cls, v):
        if v is None or isinstance(v, time) or isinstance(v, datetime):
            return v
        if isinstance(v, str):
            if "T" in v:
                vv = v.replace("Z", "+00:00")
                return datetime.fromisoformat(vv)
            for fmt in ("%H:%M:%S.%f", "%H:%M:%S", "%H:%M"):
                try:
                    return datetime.strptime(v, fmt).time()
                except ValueError:
                    pass
        raise ValueError("hora_salida inválida")
