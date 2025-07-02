"""
Manager que integra templates con el servicio de notificaciones.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from .template_engine import TemplateEngine
from .template_processor import TemplateProcessor
from ..models.notificacion_model import NotificacionModel, TipoNotificacion, DestinatarioModel


class TemplateManager:
    """Manager para integrar templates con notificaciones."""
    
    def __init__(self, template_dir: Optional[str] = None, use_css_inline: bool = True):
        """
        Inicializa el manager de templates.
        
        Args:
            template_dir: Directorio de templates personalizados
            use_css_inline: Si convertir CSS a inline automáticamente
        """
        self.engine = TemplateEngine(template_dir)
        self.processor = TemplateProcessor(use_premailer=use_css_inline)
        
        # Configuración global para todos los templates
        self.global_context = {
            'empresa_nombre': 'Hazard Service',
            'empresa_direccion': 'Dirección de tu empresa',
            'soporte_email': 'soporte@hazard.com',
            'year': datetime.now().year
        }
    
    def set_global_context(self, **context):
        """Actualiza el contexto global para todos los templates."""
        self.global_context.update(context)
    
    def create_notification_from_template(
        self,
        template_name: str,
        destinatarios: list,
        asunto: str,
        context: Dict[str, Any],
        css_file: Optional[str] = None
    ) -> NotificacionModel:
        """
        Crea una NotificacionModel usando un template.
        
        Args:
            template_name: Nombre del template (ej: "orden_completada.html")
            destinatarios: Lista de destinatarios
            asunto: Asunto del email
            context: Variables para el template
            css_file: Archivo CSS adicional
            
        Returns:
            NotificacionModel: Notificación lista para enviar
        """
        # Combinar contexto global con específico
        full_context = {**self.global_context, **context}
        
        # Renderizar contenido del template
        content = self.engine.render_template(template_name, **full_context)
        
        # Crear HTML completo usando template base
        base_template = self.processor.create_base_template(asunto)
        html_content = self.engine.render_string(
            base_template, 
            content=content,
            **full_context
        )
        
        # Procesar para email (CSS inline, etc.)
        processed_html = self.processor.process_email_html(html_content, css_file)
        
        # Crear texto plano simple (fallback)
        plain_text = self._html_to_plain_text(content)
        
        # Convertir destinatarios a DestinatarioModel si es necesario
        destinatarios_models = []
        for dest in destinatarios:
            if isinstance(dest, DestinatarioModel):
                destinatarios_models.append(dest)
            elif isinstance(dest, dict):
                destinatarios_models.append(DestinatarioModel(**dest))
            else:
                # Asumir que es un string con email
                destinatarios_models.append(DestinatarioModel(email=str(dest)))
        
        return NotificacionModel(
            tipo_canal=TipoNotificacion.EMAIL,
            asunto=asunto,
            mensaje=plain_text,
            mensaje_html=processed_html,
            destinatarios=destinatarios_models
        )
    
    def render_preview(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Renderiza un preview del template para testing.
        
        Args:
            template_name: Nombre del template
            context: Variables para el template
            
        Returns:
            str: HTML renderizado
        """
        full_context = {**self.global_context, **context}
        content = self.engine.render_template(template_name, **full_context)
        
        base_template = self.processor.create_base_template("Preview")
        return self.engine.render_string(
            base_template,
            content=content,
            **full_context
        )
    
    def list_available_templates(self) -> list[str]:
        """Lista todos los templates disponibles."""
        return self.engine.list_templates()
    
    def template_exists(self, template_name: str) -> bool:
        """Verifica si un template existe."""
        return self.engine.template_exists(template_name)
    
    def _html_to_plain_text(self, html: str) -> str:
        """Convierte HTML a texto plano simple."""
        import re
        
        # Remover tags HTML
        text = re.sub(r'<[^>]+>', '', html)
        
        # Limpiar espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        
        # Limpiar entidades HTML comunes
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        
        return text.strip()
    
    # Métodos helper para casos comunes
    def crear_orden_completada(
        self,
        destinatarios: list,
        orden_id: int,
        cliente_nombre: str,
        tecnico_nombre: str,
        edificio: str,
        **kwargs
    ) -> NotificacionModel:
        """Helper para crear notificación de orden completada."""
        context = {
            'orden_id': orden_id,
            'cliente_nombre': cliente_nombre,
            'tecnico_nombre': tecnico_nombre,
            'edificio': edificio,
            'fecha_finalizacion': datetime.now(),
            **kwargs
        }
        
        return self.create_notification_from_template(
            template_name='orden_completada.html',
            destinatarios=destinatarios,
            asunto=f'✅ Orden #{orden_id} completada - {edificio}',
            context=context
        )
    
    def crear_falla_critica(
        self,
        destinatarios: list,
        orden_id: int,
        edificio: str,
        descripcion_falla: str,
        **kwargs
    ) -> NotificacionModel:
        """Helper para crear alerta de falla crítica."""
        context = {
            'orden_id': orden_id,
            'edificio': edificio,
            'descripcion_falla': descripcion_falla,
            'timestamp': datetime.now(),
            **kwargs
        }
        
        return self.create_notification_from_template(
            template_name='falla_critica.html',
            destinatarios=destinatarios,
            asunto=f'🚨 EMERGENCIA - Falla crítica en {edificio}',
            context=context
        )
    
    def crear_asignacion_tecnico(
        self,
        destinatarios: list,
        orden_id: int,
        tecnico_nombre: str,
        cliente: str,
        ubicacion: str,
        descripcion: str,
        **kwargs
    ) -> NotificacionModel:
        """Helper para crear asignación a técnico."""
        context = {
            'orden_id': orden_id,
            'tecnico_nombre': tecnico_nombre,
            'cliente': cliente,
            'ubicacion': ubicacion,
            'descripcion': descripcion,
            'fecha_asignacion': datetime.now(),
            'prioridad': kwargs.get('prioridad', 'media'),
            **kwargs
        }
        
        return self.create_notification_from_template(
            template_name='asignacion_tecnico.html',
            destinatarios=destinatarios,
            asunto=f'🔧 Nueva asignación - Orden #{orden_id}',
            context=context
        ) 