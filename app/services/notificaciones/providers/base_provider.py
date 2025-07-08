"""
Proveedor base para notificaciones con funcionalidad común - Versión Simplificada.
"""

from abc import ABC
from typing import Dict, Any
from ..interfaces.notificador_interface import NotificadorInterface
from ..models.notificacion_model import (
    NotificacionModel, 
    ResultadoNotificacion
)


class BaseNotificacionProvider(NotificadorInterface, ABC):
    """
    Clase base simplificada que implementa funcionalidad común para todos los proveedores.
    """

    def __init__(self, configuracion: Dict[str, Any]):
        self.configuracion = configuracion
        if not self.validar_configuracion():
            raise ValueError(f"Configuración inválida para {self.obtener_tipo_canal()}")

    async def enviar(self, notificacion: NotificacionModel) -> ResultadoNotificacion:
        """Envía una notificación manejando el flujo completo."""
        try:
            self._validar_notificacion(notificacion)
            return await self._enviar_interno(notificacion)
            
        except Exception as e:
            return ResultadoNotificacion(
                exito=False,
                mensaje=str(e)
            )

    def _validar_notificacion(self, notificacion: NotificacionModel) -> None:
        """Valida que la notificación sea compatible con este proveedor."""
        if notificacion.tipo_canal != self.obtener_tipo_canal():
            raise ValueError(f"Tipo de canal incompatible")
        if not notificacion.destinatarios:
            raise ValueError("Debe tener al menos un destinatario")

    async def _enviar_interno(self, notificacion: NotificacionModel) -> ResultadoNotificacion:
        """Método que debe implementar cada proveedor específico."""
        raise NotImplementedError("Debe implementarse en la clase hija")

    def _crear_resultado_exito(self, mensaje: str = "Enviado exitosamente") -> ResultadoNotificacion:
        """Crea un resultado de éxito."""
        return ResultadoNotificacion(
            exito=True,
            mensaje=mensaje
        )

    def _crear_resultado_error(self, mensaje: str) -> ResultadoNotificacion:
        """Crea un resultado de error."""
        return ResultadoNotificacion(
            exito=False,
            mensaje=mensaje
        ) 