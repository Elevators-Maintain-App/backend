# 📧 Servicio de Notificaciones Multi-Canal

Sistema escalable de notificaciones para el backend Hazard Service que permite enviar mensajes a través de múltiples canales (email, Slack, Teams, WhatsApp, etc.) siguiendo principios SOLID y patrones de diseño.

## 🏗️ Arquitectura

El servicio está diseñado siguiendo estos patrones:

- **Strategy Pattern**: Cada canal de notificación tiene su propia estrategia de envío
- **Factory Pattern**: Creación controlada de proveedores de notificaciones
- **Template Method**: Flujo común de envío con implementaciones específicas
- **Dependency Injection**: Inyección de configuraciones y dependencias

### Estructura del proyecto

```
app/services/notificaciones/
├── __init__.py                    # Exportaciones principales
├── notificacion_service.py        # Servicio principal
├── interfaces/
│   └── notificador_interface.py   # Interfaz base para proveedores
├── models/
│   └── notificacion_model.py      # Modelos de datos
├── providers/
│   ├── base_provider.py           # Proveedor base
│   └── email/
│       └── office365_email_provider.py  # Proveedor Office 365
├── factory/
│   └── notificacion_factory.py    # Factory para crear proveedores
├── helpers/
│   └── notificacion_helper.py     # Helpers para casos comunes
├── examples/
│   └── ejemplo_uso_basico.py      # Ejemplos de uso
└── README.md                      # Esta documentación
```

## 🚀 Uso Básico

### 1. Configuración inicial

```python
from app.services.notificaciones import NotificacionService

# Configurar el servicio
configuraciones = {
    "email": {
        "username": "tu_email@empresa.com",
        "password": "tu_app_password",  # Usar App Password para Office 365
        "nombre_remitente": "Sistema Hazard"
    }
}

servicio = NotificacionService(configuraciones)
```

### 2. Envío simple

```python
from app.services.notificaciones.models import (
    NotificacionModel,
    TipoNotificacion,
    DestinatarioModel
)

# Crear notificación
notificacion = NotificacionModel(
    tipo_canal=TipoNotificacion.EMAIL,
    asunto="Orden completada",
    mensaje="Su orden #123 ha sido completada exitosamente.",
    destinatarios=[
        DestinatarioModel(
            nombre="Cliente Test",
            email="cliente@ejemplo.com"
        )
    ]
)

# Enviar
resultado = await servicio.enviar_notificacion(notificacion)
print(f"Éxito: {resultado.exito}")
```

### 3. Usando helpers para casos comunes

```python
from app.services.notificaciones.helpers import NotificacionHelper

helper = NotificacionHelper(servicio)

# Notificar orden completada
resultado = await helper.notificar_orden_completada(
    orden_id=12345,
    cliente_email="cliente@ejemplo.com",
    cliente_nombre="Juan Pérez",
    tecnico_nombre="Carlos López",
    edificio="Torre Plaza",
    detalles_adicionales="Mantenimiento preventivo completado sin incidencias."
)
```

## 🔧 Configuración de Office 365

Para usar email con Office 365:

### 1. Obtener App Password

1. Ve a [https://account.microsoft.com/security](https://account.microsoft.com/security)
2. Inicia sesión con tu cuenta de Office 365
3. Selecciona "Opciones de seguridad adicionales"
4. En "Contraseñas de aplicación", selecciona "Crear una nueva contraseña de aplicación"
5. Guarda la contraseña generada

### 2. Configurar el servicio

```python
configuraciones = {
    "email": {
        "username": "tu_email@empresa.com",
        "password": "la_app_password_generada",
        "smtp_server": "smtp.office365.com",  # Por defecto
        "smtp_port": 587,                     # Por defecto
        "use_tls": True,                      # Por defecto
        "timeout": 30,                        # Por defecto
        "nombre_remitente": "Sistema Hazard - Mantenimiento"
    }
}
```

## 📝 Casos de Uso del Sistema Hazard

### 1. Notificación de orden completada

```python
helper = NotificacionHelper(servicio)

resultado = await helper.notificar_orden_completada(
    orden_id=12345,
    cliente_email="admin@edificio.com",
    cliente_nombre="María García",
    tecnico_nombre="Juan Pérez",
    edificio="Torre Empresarial Centro"
)
```

### 2. Alerta de falla crítica

```python
contactos_emergencia = [
    {"nombre": "Supervisor", "email": "supervisor@edificio.com"},
    {"nombre": "Administrador", "email": "admin@edificio.com"}
]

resultados = await helper.notificar_falla_critica(
    orden_id=99999,
    contactos_emergencia=contactos_emergencia,
    edificio="Torre Empresarial Centro",
    descripcion_falla="Motor del ascensor presenta ruidos anómalos"
)
```

### 3. Mantenimiento programado

```python
from datetime import datetime

clientes = [
    {"nombre": "Admin Edificio", "email": "admin@edificio.com"}
]

resultados = await helper.notificar_mantenimiento_programado(
    clientes_emails=clientes,
    fecha_mantenimiento=datetime(2024, 2, 15, 8, 0),
    edificio="Torre Empresarial Centro",
    duracion_estimada="3 horas",
    tipo_mantenimiento="preventivo"
)
```

### 4. Asignación a técnico

```python
resultado = await helper.notificar_asignacion_orden(
    tecnico_email="tecnico@hazard.com",
    tecnico_nombre="Carlos López",
    orden_id=12346,
    cliente="Edificio Torre Plaza",
    ubicacion="Av. Principal 123, Piso 15",
    descripcion_trabajo="Revisión mensual de motor y cables",
    fecha_programada=datetime(2024, 2, 20, 9, 0)
)
```

## 🔄 Envío Masivo y Reintentos

### Envío masivo

```python
notificaciones = [notif1, notif2, notif3]  # Lista de NotificacionModel

resultados = await servicio.enviar_masivo(
    notificaciones,
    concurrencia_maxima=10  # Máximo 10 envíos simultáneos
)

exitosos = sum(1 for r in resultados if r.exito)
print(f"Enviados: {exitosos}/{len(resultados)}")
```

### Reintentos automáticos

```python
resultado = await servicio.enviar_con_reintentos(
    notificacion,
    intervalo_reintento=300  # 5 minutos entre reintentos
)
```

## 📊 Monitoreo y Estadísticas

```python
# Obtener estadísticas
stats = servicio.obtener_estadisticas()
print(f"Total enviadas: {stats['total_enviadas']}")
print(f"Total fallidas: {stats['total_fallidas']}")
print(f"Por canal: {stats['por_canal']}")

# Verificar canales configurados
canales = servicio.obtener_canales_configurados()
print(f"Canales activos: {canales}")
```

## ➕ Agregar Nuevos Canales

Para agregar un nuevo canal (ej: Telegram), sigue estos pasos:

### 1. Crear el proveedor

```python
# providers/telegram/telegram_provider.py
from ..base_provider import BaseNotificacionProvider
from ...models.notificacion_model import TipoNotificacion

class TelegramProvider(BaseNotificacionProvider):
    def obtener_tipo_canal(self) -> str:
        return TipoNotificacion.TELEGRAM.value

    def validar_configuracion(self) -> bool:
        return "bot_token" in self.configuracion

    async def _enviar_interno(self, datos) -> ResultadoNotificacion:
        # Implementar lógica específica de Telegram
        pass
```

### 2. Registrar en el factory

```python
# factory/notificacion_factory.py
from ..providers.telegram.telegram_provider import TelegramProvider

def _registrar_proveedores_default(self) -> None:
    self.registrar_proveedor(TipoNotificacion.EMAIL.value, Office365EmailProvider)
    self.registrar_proveedor(TipoNotificacion.TELEGRAM.value, TelegramProvider)
```

### 3. Agregar tipo al enum

```python
# models/notificacion_model.py
class TipoNotificacion(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"  # ← Nuevo
    SMS = "sms"
```

### 4. Configurar y usar

```python
configuraciones = {
    "email": {...},
    "telegram": {
        "bot_token": "tu_bot_token",
        "chat_id": "tu_chat_id"
    }
}

servicio = NotificacionService(configuraciones)

notificacion = NotificacionModel(
    tipo_canal=TipoNotificacion.TELEGRAM,  # ← Usar nuevo canal
    mensaje="Hola desde Telegram!",
    destinatarios=[...]
)
```

## 🧪 Testing

### Ejecutar ejemplos

```bash
# Navegar al directorio del proyecto
cd app/services/notificaciones/examples

# Editar credenciales en ejemplo_uso_basico.py
# Ejecutar ejemplos
python ejemplo_uso_basico.py
```

### Pruebas unitarias

```python
import pytest
from app.services.notificaciones import NotificacionService
from app.services.notificaciones.models import *

@pytest.mark.asyncio
async def test_envio_email():
    configuraciones = {"email": {"username": "test", "password": "test"}}
    servicio = NotificacionService(configuraciones)

    notificacion = NotificacionModel(
        tipo_canal=TipoNotificacion.EMAIL,
        asunto="Test",
        mensaje="Mensaje de prueba",
        destinatarios=[DestinatarioModel(email="test@test.com")]
    )

    # Mock del envío para testing
    resultado = await servicio.enviar_notificacion(notificacion)
    assert isinstance(resultado, ResultadoNotificacion)
```

## 🔒 Consideraciones de Seguridad

1. **Credenciales**: Nunca hardcodees credenciales en el código. Usa variables de entorno.

```python
import os

configuraciones = {
    "email": {
        "username": os.getenv("EMAIL_USERNAME"),
        "password": os.getenv("EMAIL_PASSWORD")
    }
}
```

2. **App Passwords**: Para Office 365, siempre usa App Passwords, no la contraseña principal.

3. **Rate Limiting**: El servicio incluye control de concurrencia para evitar spam.

4. **Logs**: Evita loggear información sensible como contraseñas o contenido de mensajes.

## 🐛 Troubleshooting

### Email no se envía

1. **Verifica credenciales**: Asegúrate de usar App Password para Office 365
2. **Verifica configuración**: Confirma server y puerto (smtp.office365.com:587)
3. **Verifica TLS**: Office 365 requiere TLS habilitado
4. **Revisa logs**: Activa debug=True en la configuración

### Error de autenticación

```python
# Habilitar logs detallados
configuraciones = {
    "email": {
        "username": "tu_email@empresa.com",
        "password": "app_password",
        "debug": True  # ← Habilitar debug
    }
}
```

### Destinatarios rechazados

- Verifica que los emails sean válidos
- Confirma que el remitente tenga permisos
- Revisa las políticas de spam del servidor

## 📚 Referencias

- [Office 365 SMTP Settings](https://docs.microsoft.com/en-us/exchange/mail-flow-best-practices/how-to-set-up-a-multifunction-device-or-application-to-send-email-using-microsoft-365-or-office-365)
- [Python smtplib Documentation](https://docs.python.org/3/library/smtplib.html)
- [Strategy Pattern](https://refactoring.guru/design-patterns/strategy)
- [Factory Pattern](https://refactoring.guru/design-patterns/factory-method)

---

🎯 **El servicio está listo para usar y extender fácilmente con nuevos canales de notificación.**
