"""
Interfaz base para todos los proveedores de notificaciones.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from ..models.notificacion_model import NotificacionModel, ResultadoNotificacion


class NotificadorInterface(ABC):
    """
    Interfaz que deben implementar todos los proveedores de notificaciones.
    Siguiendo el Strategy Pattern para permitir diferentes canales.
    """

    @abstractmethod
    async def enviar(self, notificacion: NotificacionModel) -> ResultadoNotificacion:
        """
        Envía una notificación a través del canal específico.
        
        Args:
            notificacion: Datos de la notificación a enviar
            
        Returns:
            ResultadoNotificacion: Resultado del envío
        """
        pass

    @abstractmethod
    def validar_configuracion(self) -> bool:
        """
        Valida que la configuración del proveedor sea correcta.
        
        Returns:
            bool: True si la configuración es válida
        """
        pass

    @abstractmethod
    def obtener_tipo_canal(self) -> str:
        """
        Retorna el tipo de canal que maneja este proveedor.
        
        Returns:
            str: Nombre del canal (email, slack, teams, etc.)
        """
        pass

    def obtener_configuracion_requerida(self) -> Dict[str, Any]:
        """
        Retorna la configuración requerida por este proveedor.
        Puede ser sobrescrito por implementaciones específicas.
        
        Returns:
            Dict: Configuración requerida
        """
        return {} 