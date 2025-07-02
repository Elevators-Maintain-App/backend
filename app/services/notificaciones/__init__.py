"""
Servicio de notificaciones multi-canal para el sistema Hazard.

Arquitectura escalable que sigue Strategy Pattern y Factory Pattern.
🎯 NUEVO: Auto-configuración desde variables de entorno.

Uso básico auto-configurado:

```python
from app.services.notificaciones import NotificacionService
from app.services.notificaciones.models import NotificacionModel, TipoNotificacion, DestinatarioModel

# ✨ NUEVO: Sin configuraciones manuales - todo desde environment
servicio = NotificacionService(TipoNotificacion.EMAIL)

# Verificar disponibilidad
if servicio.is_canal_disponible(TipoNotificacion.EMAIL):
    notificacion = NotificacionModel(
        tipo_canal=TipoNotificacion.EMAIL,
        asunto="Orden completada",
        mensaje="La orden #123 ha sido completada.",
        destinatarios=[DestinatarioModel(nombre="Cliente", email="cliente@ejemplo.com")]
    )
    
    resultado = await servicio.enviar_notificacion(notificacion)
```

Auto-configuración global:

```python
# Configura automáticamente todos los canales disponibles
servicio = NotificacionService()

print(f"Canales disponibles: {servicio.obtener_canales_disponibles()}")
print(f"Canales configurados: {servicio.obtener_canales_configurados()}")
```

Uso con templates:

```python
from app.services.notificaciones import TemplateManager

template_manager = TemplateManager()
notificacion = template_manager.crear_orden_completada(
    destinatarios=[DestinatarioModel(email="cliente@ejemplo.com")],
    orden_id=123,
    cliente_nombre="Juan Pérez",
    tecnico_nombre="Carlos",
    edificio="Torre Norte"
)

servicio = NotificacionService(TipoNotificacion.EMAIL)
resultado = await servicio.enviar_notificacion(notificacion)
```

Variables de entorno requeridas:

```bash
NOTIFICATION_EMAIL=tu_email@empresa.com
EMAIL_PWD=tu_password_o_app_password
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
EMAIL_TIMEOUT=30
```

Para agregar nuevos canales:
1. Crear proveedor que implemente NotificadorInterface
2. Registrarlo en el factory
3. Agregar método _configurar_nuevo_canal() en NotificacionService
4. ¡Automáticamente disponible!
"""

from .notificacion_service import NotificacionService
from .factory import NotificacionFactory
from .models import (
    NotificacionModel,
    ResultadoNotificacion,
    TipoNotificacion,
    DestinatarioModel
)
from .interfaces import NotificadorInterface
from .providers import Office365EmailProvider
from .templates import TemplateManager

__all__ = [
    "NotificacionService",
    "NotificacionFactory",
    "NotificacionModel",
    "ResultadoNotificacion", 
    "TipoNotificacion",
    "DestinatarioModel",
    "NotificadorInterface",
    "Office365EmailProvider",
    "TemplateManager"
]
