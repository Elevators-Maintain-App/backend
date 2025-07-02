"""
Modelos de datos para el sistema de notificaciones - Versión Simplificada.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class TipoNotificacion(str, Enum):
    """Tipos de notificación disponibles."""
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    SMS = "sms"


class DestinatarioModel(BaseModel):
    """Modelo para representar un destinatario de notificación."""
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    

class NotificacionModel(BaseModel):
    """
    Modelo simplificado para una notificación.
    """
    tipo_canal: TipoNotificacion
    asunto: str = Field(..., description="Asunto o título de la notificación")
    mensaje: str = Field(..., description="Contenido principal del mensaje")
    mensaje_html: Optional[str] = None
    destinatarios: List[DestinatarioModel] = Field(..., min_items=1)
    remitente: Optional[DestinatarioModel] = None

    class Config:
        use_enum_values = True


class ResultadoNotificacion(BaseModel):
    """Resultado simplificado del envío de una notificación."""
    exito: bool
    mensaje: str
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True 