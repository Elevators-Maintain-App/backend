"""
Factory para crear proveedores de notificaciones.
"""

from typing import Dict, Any, Type, List

from ..interfaces.notificador_interface import NotificadorInterface
from ..models.notificacion_model import TipoNotificacion
from ..providers.email.office365_email_provider import Office365EmailProvider
from app.core.config import settings

class NotificacionFactory:
    """Factory para crear instancias de proveedores de notificaciones."""

    def __init__(self):
        self._proveedores: Dict[str, Type[NotificadorInterface]] = {}
        self._configuraciones: Dict[str, Dict[str, Any]] = {}
        self._registrar_proveedores_default()

    def _registrar_proveedores_default(self) -> None:
        """Registra los proveedores por defecto."""
        self.registrar_proveedor(TipoNotificacion.EMAIL.value, Office365EmailProvider)
        
        # Configurar email por defecto solo si hay credenciales
        if settings.notification_email and settings.email_password:
            self.configurar_proveedor(TipoNotificacion.EMAIL.value, {
                "username": settings.notification_email,
                "password": settings.email_password,
                "smtp_server": settings.smtp_server or "smtp.office365.com",
                "smtp_port": int(settings.smtp_port) if settings.smtp_port else 587,
                "use_tls": True,
                "timeout": settings.email_timeout
            })

    def registrar_proveedor(self, tipo_canal: str, clase_proveedor: Type[NotificadorInterface]) -> None:
        """Registra un nuevo proveedor."""
        if not issubclass(clase_proveedor, NotificadorInterface):
            raise ValueError(f"Debe implementar NotificadorInterface")
        self._proveedores[tipo_canal] = clase_proveedor
        # Solo registrar el proveedor, la configuración se establecerá cuando se configure

    def configurar_proveedor(self, tipo_canal: str, configuracion: Dict[str, Any]) -> None:
        """Configura un proveedor específico."""
        if tipo_canal not in self._proveedores:
            raise ValueError(f"Proveedor no registrado: {tipo_canal}")
        self._configuraciones[tipo_canal] = configuracion

    def crear_notificador(self, tipo_canal: str) -> NotificadorInterface:
        """Crea una instancia del notificador."""
        if tipo_canal not in self._proveedores:
            raise ValueError(f"Proveedor no disponible: {tipo_canal}")
        
        if tipo_canal not in self._configuraciones:
            raise ValueError(f"Proveedor no configurado: {tipo_canal}")
        
        clase_proveedor = self._proveedores[tipo_canal]
        configuracion = self._configuraciones[tipo_canal]
        return clase_proveedor(configuracion)

    def obtener_tipos_disponibles(self) -> List[str]:
        """Lista de tipos de canales disponibles."""
        return list(self._proveedores.keys())

    def esta_configurado(self, tipo_canal: str) -> bool:
        """Verifica si un canal está configurado."""
        return (tipo_canal in self._proveedores and 
                tipo_canal in self._configuraciones) 