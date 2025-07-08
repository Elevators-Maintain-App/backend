"""
Ejemplos de uso del sistema de templates para notificaciones.
"""

import asyncio
from app.services.notificaciones import NotificacionService
from app.services.notificaciones.templates import TemplateManager
from app.services.notificaciones.models.notificacion_model import DestinatarioModel


async def ejemplo_template_orden_completada():
    """Ejemplo usando template para orden completada."""
    print("📧 Ejemplo: Template orden completada")
    
    # Configuración del servicio
    configuraciones = {
        "email": {
            "username": "sistema@hazard.com",
            "password": "tu_app_password"
        }
    }
    
    servicio = NotificacionService(configuraciones)
    template_manager = TemplateManager()
    
    # Crear notificación desde template
    notificacion = template_manager.crear_orden_completada(
        destinatarios=[DestinatarioModel(email="cliente@edificio.com", nombre="María García")],
        orden_id=12345,
        cliente_nombre="María García",
        tecnico_nombre="Juan Pérez",
        edificio="Torre Plaza",
        unidad="Ascensor Principal",
        observaciones="Todo en perfecto estado"
    )
    
    # Enviar
    resultado = await servicio.enviar_notificacion(notificacion)
    
    if resultado.exito:
        print("✅ Email con template enviado exitosamente")
    else:
        print(f"❌ Error: {resultado.mensaje}")


async def ejemplo_template_falla_critica():
    """Ejemplo usando template para falla crítica."""
    print("\n🚨 Ejemplo: Template falla crítica")
    
    configuraciones = {
        "email": {
            "username": "emergencias@hazard.com",
            "password": "tu_app_password"
        }
    }
    
    servicio = NotificacionService(configuraciones)
    template_manager = TemplateManager()
    
    # Crear notificación de emergencia
    notificacion = template_manager.crear_falla_critica(
        destinatarios=[
            DestinatarioModel(email="admin@edificio.com", nombre="Administrador"),
            DestinatarioModel(email="seguridad@edificio.com", nombre="Seguridad")
        ],
        orden_id=67890,
        descripcion_falla="Motor principal sobrecalentado",
        edificio="Torre Norte",
        acciones_requeridas="Suspender uso inmediato y contactar técnico especializado",
        contacto_tecnico="Carlos López - 555-0123"
    )
    
    resultado = await servicio.enviar_notificacion(notificacion)
    
    if resultado.exito:
        print("✅ Alerta de emergencia enviada")
    else:
        print(f"❌ Error: {resultado.mensaje}")


async def ejemplo_template_asignacion():
    """Ejemplo usando template para asignación técnico."""
    print("\n🔧 Ejemplo: Template asignación técnico")
    
    configuraciones = {
        "email": {
            "username": "asignaciones@hazard.com",
            "password": "tu_app_password"
        }
    }
    
    servicio = NotificacionService(configuraciones)
    template_manager = TemplateManager()
    
    # Crear notificación de asignación
    notificacion = template_manager.crear_asignacion_tecnico(
        destinatarios=[DestinatarioModel(email="tecnico@hazard.com", nombre="Carlos López")],
        orden_id=54321,
        tecnico_nombre="Carlos López",
        cliente_nombre="Edificio Empresarial ABC",
        ubicacion="Av. Principal #123",
        descripcion_trabajo="Mantenimiento preventivo mensual",
        materiales_necesarios="Kit básico de herramientas, aceite lubricante",
        contacto_cliente="Ana Ruiz - 555-9876"
    )
    
    resultado = await servicio.enviar_notificacion(notificacion)
    
    if resultado.exito:
        print("✅ Asignación enviada al técnico")
    else:
        print(f"❌ Error: {resultado.mensaje}")


if __name__ == "__main__":
    print("🎨 Ejemplos de templates para notificaciones\n")
    
    # Para probar, descomenta las siguientes líneas y actualiza credenciales:
    # asyncio.run(ejemplo_template_orden_completada())
    # asyncio.run(ejemplo_template_falla_critica())
    # asyncio.run(ejemplo_template_asignacion())
    
    print("💡 Para probar:")
    print("1. Actualiza credenciales en los ejemplos")
    print("2. Descomenta las líneas de asyncio.run()")
    print("3. Ejecuta el archivo")
    print("4. Los emails tendrán formato HTML profesional") 