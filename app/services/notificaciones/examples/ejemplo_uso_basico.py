"""
Ejemplos del servicio de notificaciones auto-configurado.
"""

import asyncio
from ..notificacion_service import NotificacionService
from ..models.notificacion_model import (
    NotificacionModel,
    TipoNotificacion,
    DestinatarioModel
)


async def ejemplo_email_basico():
    """Ejemplo básico de envío de email auto-configurado."""
    print("📧 Ejemplo: Envío básico de email auto-configurado")
    
    # ¡Sin configuraciones! Todo desde variables de entorno
    servicio = NotificacionService(TipoNotificacion.EMAIL)
    
    # Verificar disponibilidad
    if not servicio.is_canal_disponible(TipoNotificacion.EMAIL):
        print("❌ Email no configurado. Configura NOTIFICATION_EMAIL y EMAIL_PWD")
        return
    
    # Crear notificación
    notificacion = NotificacionModel(
        tipo_canal=TipoNotificacion.EMAIL,
        asunto="🔧 Orden #12345 completada",
        mensaje="El mantenimiento ha sido completado exitosamente.",
        destinatarios=[
            DestinatarioModel(nombre="Cliente Test", email="cliente@ejemplo.com")
        ]
    )
    
    # Enviar
    resultado = await servicio.enviar_notificacion(notificacion)
    
    if resultado.exito:
        print("✅ Email enviado exitosamente")
    else:
        print(f"❌ Error: {resultado.mensaje}")


async def ejemplo_servicio_global():
    """Ejemplo usando servicio con todos los canales disponibles."""
    print("\n🌐 Ejemplo: Servicio con auto-configuración global")
    
    # Auto-configura todos los canales disponibles desde environment
    servicio = NotificacionService()
    
    print(f"📡 Canales disponibles: {servicio.obtener_canales_disponibles()}")
    print(f"✅ Canales configurados: {servicio.obtener_canales_configurados()}")
    
    if TipoNotificacion.EMAIL.value in servicio.obtener_canales_configurados():
        print("📧 Email está listo para usar")
    else:
        print("⚠️ Email no está configurado")


async def ejemplo_masivo():
    """Ejemplo de envío masivo auto-configurado."""
    print("\n📨 Ejemplo: Envío masivo auto-configurado")
    
    servicio = NotificacionService(TipoNotificacion.EMAIL)
    
    if not servicio.is_canal_disponible(TipoNotificacion.EMAIL):
        print("❌ Email no configurado para envío masivo")
        return
    
    # Múltiples notificaciones
    notificaciones = [
        NotificacionModel(
            tipo_canal=TipoNotificacion.EMAIL,
            asunto="🚨 Falla crítica",
            mensaje="Emergencia en ascensor",
            destinatarios=[DestinatarioModel(email="emergencia@cliente.com")]
        ),
        NotificacionModel(
            tipo_canal=TipoNotificacion.EMAIL,
            asunto="📅 Mantenimiento programado",
            mensaje="Recordatorio de mantenimiento",
            destinatarios=[DestinatarioModel(email="admin@cliente.com")]
        )
    ]
    
    resultados = await servicio.enviar_masivo(notificaciones)
    exitosos = sum(1 for r in resultados if r.exito)
    print(f"Enviados: {exitosos}/{len(resultados)}")


if __name__ == "__main__":
    print("🎯 Ejemplos del servicio de notificaciones auto-configurado\n")
    
    # Para probar, configura las variables de entorno:
    # NOTIFICATION_EMAIL=tu_email@empresa.com
    # EMAIL_PWD=tu_password
    # SMTP_SERVER=smtp.office365.com
    # SMTP_PORT=587
    # EMAIL_TIMEOUT=30
    
    # Luego descomenta las líneas siguientes:
    # asyncio.run(ejemplo_email_basico())
    # asyncio.run(ejemplo_servicio_global())
    # asyncio.run(ejemplo_masivo())
    
    print("💡 Para probar:")
    print("1. Configura las variables de entorno de email")
    print("2. Descomenta las líneas de asyncio.run()")
    print("3. Ejecuta el archivo")
    print("4. ¡Sin configuraciones manuales necesarias!") 