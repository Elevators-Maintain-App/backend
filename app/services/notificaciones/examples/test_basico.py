"""
Test básico para validar el módulo de notificaciones auto-configurado.
"""

import asyncio
import os
from app.services.notificaciones import NotificacionService
from app.services.notificaciones.models import NotificacionModel, TipoNotificacion, DestinatarioModel


async def test_email_auto_configurado():
    """Test básico de envío de email auto-configurado."""
    
    print("🧪 Probando servicio auto-configurado...")
    
    try:
        # Crear servicio auto-configurado (lee desde variables de entorno)
        servicio = NotificacionService(TipoNotificacion.EMAIL)
        
        # Verificar si está configurado
        if not servicio.is_canal_disponible(TipoNotificacion.EMAIL):
            print("❌ Email no configurado")
            print("💡 Configura estas variables de entorno:")
            print("   NOTIFICATION_EMAIL=tu_email@empresa.com")
            print("   EMAIL_PWD=tu_password")
            print("   SMTP_SERVER=smtp.office365.com")
            print("   SMTP_PORT=587")
            print("   EMAIL_TIMEOUT=30")
            return
        
        print(f"✅ Email configurado desde environment")
        print(f"📡 Canales disponibles: {servicio.obtener_canales_disponibles()}")
        print(f"🔧 Canales configurados: {servicio.obtener_canales_configurados()}")
        
        # Crear notificación
        notificacion = NotificacionModel(
            tipo_canal=TipoNotificacion.EMAIL,
            asunto="✅ Test del sistema auto-configurado",
            mensaje="Este es un mensaje de prueba del sistema auto-configurado de notificaciones.",
            destinatarios=[
                DestinatarioModel(
                    email="destino@ejemplo.com",  # Cambiar por email de destino real
                    nombre="Usuario de Prueba"
                )
            ]
        )
        
        # Enviar
        print("📤 Enviando notificación...")
        resultado = await servicio.enviar_notificacion(notificacion)
        
        if resultado.exito:
            print("✅ Email enviado exitosamente")
            print(f"📧 Detalles: {resultado.mensaje}")
        else:
            print("❌ Error al enviar email")
            print(f"🚨 Error: {resultado.mensaje}")
            
    except Exception as e:
        print(f"💥 Excepción: {str(e)}")


async def test_multiples_canales():
    """Test de configuración automática de múltiples canales."""
    
    print("\n🌐 Probando auto-configuración global...")
    
    try:
        # Servicio global (auto-configura todos los canales)
        servicio = NotificacionService()
        
        print(f"📡 Canales registrados: {servicio.obtener_canales_disponibles()}")
        print(f"✅ Canales configurados: {servicio.obtener_canales_configurados()}")
        
        for canal in servicio.obtener_canales_disponibles():
            disponible = servicio.is_canal_disponible(canal)
            estado = "✅ Configurado" if disponible else "⚠️ No configurado"
            print(f"   {canal}: {estado}")
            
    except Exception as e:
        print(f"💥 Error: {str(e)}")


if __name__ == "__main__":
    print("🧪 Test básico del módulo de notificaciones auto-configurado")
    print("=" * 60)
    
    # Ejecutar tests
    asyncio.run(test_email_auto_configurado())
    asyncio.run(test_multiples_canales())
    
    print("\n✨ ¡Tests completados!")
    print("\n💡 Ventajas del sistema auto-configurado:")
    print("   ✅ Sin configuraciones manuales")
    print("   ✅ Configuración desde variables de entorno")
    print("   ✅ Fácil de usar: NotificacionService(TipoNotificacion.EMAIL)")
    print("   ✅ Detección automática de canales disponibles") 