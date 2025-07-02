"""
Proveedor de notificaciones por email usando Office 365 - Versión Simplificada.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List

from ..base_provider import BaseNotificacionProvider
from ...models.notificacion_model import (
    NotificacionModel, 
    ResultadoNotificacion, 
    TipoNotificacion,
    DestinatarioModel
)

from app.core.config import settings


class Office365EmailProvider(BaseNotificacionProvider):
    """Proveedor de email simplificado para Office 365 usando SMTP."""

    def __init__(self, configuracion: Dict[str, Any]):
        config_default = {
            "smtp_server": settings.smtp_server,
            "smtp_port": settings.smtp_port,
            "use_tls": True,
            "timeout": settings.email_timeout
        }
        configuracion_final = {**config_default, **configuracion}
        super().__init__(configuracion_final)

    def validar_configuracion(self) -> bool:
        """Valida la configuración de Office 365."""
        required = ["username", "password"]
        return all(self.configuracion.get(field) for field in required)

    def obtener_tipo_canal(self) -> str:
        return TipoNotificacion.EMAIL

    def obtener_configuracion_requerida(self) -> Dict[str, Any]:
        return {
            "username": "soporte@verti-one.com",
            "password": "Contraseña o App Password",
            "smtp_server": "Servidor SMTP (default: smtp.office365.com)",
            "smtp_port": "Puerto SMTP (default: 587)"
        }

    async def _enviar_interno(self, notificacion: NotificacionModel) -> ResultadoNotificacion:
        """Envía el email usando SMTP de Office 365."""
        try:
            # Validar destinatarios
            destinatarios_email = []
            for dest in notificacion.destinatarios:
                if not dest.email:
                    raise ValueError(f"Destinatario sin email: {dest.nombre}")
                destinatarios_email.append(dest.email)

            # Preparar remitente
            remitente = notificacion.remitente
            if not remitente or not remitente.email:
                remitente = DestinatarioModel(
                    email=self.configuracion["username"],
                    nombre=self.configuracion.get("nombre_remitente", "Sistema Hazard")
                )

            # Crear y enviar mensaje
            mensaje = self._crear_mensaje(notificacion, remitente, destinatarios_email)
            
            with self._crear_conexion_smtp() as servidor:
                servidor.login(self.configuracion["username"], self.configuracion["password"])
                servidor.send_message(mensaje)
                
                return self._crear_resultado_exito(
                    f"Email enviado a {len(destinatarios_email)} destinatarios"
                )

        except smtplib.SMTPAuthenticationError:
            return self._crear_resultado_error("Error de autenticación")
        except smtplib.SMTPRecipientsRefused as e:
            return self._crear_resultado_error(f"Destinatarios rechazados: {e.recipients}")
        except Exception as e:
            return self._crear_resultado_error(f"Error: {str(e)}")

    def _crear_mensaje(
        self, 
        notificacion: NotificacionModel, 
        remitente: DestinatarioModel,
        destinatarios_email: List[str]
    ) -> MIMEMultipart:
        """Crea el mensaje de email."""
        mensaje = MIMEMultipart("alternative")
        
        # Headers
        mensaje["Subject"] = notificacion.asunto
        mensaje["From"] = f"{remitente.nombre} <{remitente.email}>" if remitente.nombre else str(remitente.email)
        mensaje["To"] = ", ".join(destinatarios_email)
        
        # Contenido texto
        mensaje.attach(MIMEText(notificacion.mensaje, "plain", "utf-8"))
        
        # Contenido HTML si existe
        if notificacion.mensaje_html:
            mensaje.attach(MIMEText(notificacion.mensaje_html, "html", "utf-8"))
        
        return mensaje

    def _crear_conexion_smtp(self) -> smtplib.SMTP:
        """Crea la conexión SMTP."""
        servidor = smtplib.SMTP(
            self.configuracion["smtp_server"], 
            self.configuracion["smtp_port"],
            timeout=self.configuracion["timeout"]
        )
        
        if self.configuracion["use_tls"]:
            context = ssl.create_default_context()
            servidor.starttls(context=context)
        
        return servidor 