"""
Proveedores de notificaciones para diferentes canales.
"""

from .base_provider import BaseNotificacionProvider
from .email.office365_email_provider import Office365EmailProvider

__all__ = [
    "BaseNotificacionProvider",
    "Office365EmailProvider"
] 