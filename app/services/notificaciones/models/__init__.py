"""
Modelos de datos para el servicio de notificaciones.
"""

from .notificacion_model import (
    NotificacionModel,
    ResultadoNotificacion,
    TipoNotificacion,
    DestinatarioModel
)

__all__ = [
    "NotificacionModel",
    "ResultadoNotificacion", 
    "TipoNotificacion",
    "DestinatarioModel"
] 