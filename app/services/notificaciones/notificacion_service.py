"""
Servicio principal de notificaciones - Versión Auto-configurada.
"""

import asyncio
from typing import List, Optional, Union
from app.core.config import settings

from .factory.notificacion_factory import NotificacionFactory
from .models.notificacion_model import (
    NotificacionModel,
    ResultadoNotificacion,
    TipoNotificacion
)


class NotificacionService:
    """Servicio auto-configurado para manejar notificaciones multi-canal."""

    def __init__(self, tipo_canal: Optional[Union[str, TipoNotificacion]] = None):
        """
        Inicializa el servicio con configuración automática desde variables de entorno.
        
        Args:
            tipo_canal: Tipo específico a configurar. Si es None, configura todos los disponibles.
        """
        self.factory = NotificacionFactory()
        self._configurar_desde_environment(tipo_canal)

    def _configurar_desde_environment(self, tipo_canal: Optional[Union[str, TipoNotificacion]] = None) -> None:
        """Configura proveedores automáticamente desde variables de entorno."""
        
        # Normalizar tipo_canal si se proporciona
        if tipo_canal:
            if isinstance(tipo_canal, TipoNotificacion):
                tipo_canal = tipo_canal.value
            
            # Configurar solo el tipo específico
            if tipo_canal == TipoNotificacion.EMAIL.value:
                self._configurar_email()
        else:
            # Configurar todos los canales disponibles
            self._configurar_email()
            # Aquí se pueden agregar más canales en el futuro:
            # self._configurar_slack()
            # self._configurar_teams()
            # etc.

    def _configurar_email(self) -> None:
        """Configura el proveedor de email desde variables de entorno."""
        if not settings.notification_email or not settings.email_password:
            return  # Sin configuración, simplemente no configurar el proveedor
        
        configuracion_email = {
            "username": settings.notification_email,
            "password": settings.email_password,
            "smtp_server": settings.smtp_server or "smtp.office365.com",
            "smtp_port": int(settings.smtp_port) if settings.smtp_port else 587,
            "use_tls": True,
            "timeout": settings.email_timeout,
            "nombre_remitente": "Sistema Hazard"
        }
        
        try:
            self.factory.configurar_proveedor(TipoNotificacion.EMAIL.value, configuracion_email)
        except Exception:
            # Si falla la configuración, simplemente no está disponible
            pass

    async def enviar_notificacion(self, notificacion: NotificacionModel) -> ResultadoNotificacion:
        """Envía una notificación."""
        try:
            notificador = self.factory.crear_notificador(notificacion.tipo_canal)
            return await notificador.enviar(notificacion)
            
        except Exception as e:
            print("** error", e)
            return ResultadoNotificacion(
                exito=False,
                mensaje=str(e)
            )

    async def enviar_masivo(
        self, 
        notificaciones: List[NotificacionModel],
        concurrencia_maxima: int = 10
    ) -> List[ResultadoNotificacion]:
        """Envía múltiples notificaciones concurrentemente."""
        semaforo = asyncio.Semaphore(concurrencia_maxima)
        
        async def enviar_con_limite(notif: NotificacionModel) -> ResultadoNotificacion:
            async with semaforo:
                return await self.enviar_notificacion(notif)
        
        resultados = await asyncio.gather(
            *[enviar_con_limite(notif) for notif in notificaciones],
            return_exceptions=True
        )
        
        # Procesar excepciones
        resultados_procesados = []
        for resultado in resultados:
            if isinstance(resultado, Exception):
                resultado_error = ResultadoNotificacion(
                    exito=False,
                    mensaje=str(resultado)
                )
                resultados_procesados.append(resultado_error)
            else:
                resultados_procesados.append(resultado)
        
        return resultados_procesados

    def obtener_canales_disponibles(self) -> List[str]:
        """Lista de canales disponibles."""
        return self.factory.obtener_tipos_disponibles()

    def obtener_canales_configurados(self) -> List[str]:
        """Lista de canales configurados."""
        return [canal for canal in self.factory.obtener_tipos_disponibles() 
                if self.factory.esta_configurado(canal)]
    
    def is_canal_disponible(self, tipo_canal: Union[str, TipoNotificacion]) -> bool:
        """Verifica si un canal específico está disponible y configurado."""
        if isinstance(tipo_canal, TipoNotificacion):
            tipo_canal = tipo_canal.value
        return tipo_canal in self.obtener_canales_configurados() 