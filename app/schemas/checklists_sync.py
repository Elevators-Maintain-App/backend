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

    hora_entrada: Optional[datetime] = None
    hora_salida: Optional[datetime] = None

    observaciones: Optional[str] = None
    firma_tecnico: Optional[str] = None
    firma_cliente: Optional[str] = None
    check_metadata: Dict[str, Any] = Field(default_factory=dict)

    items: List[ChecklistItemSync]

    lat: Optional[float] = None
    lon: Optional[float] = None