"""
Motor de templates para emails usando Jinja2.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template


class TemplateEngine:
    """Motor de templates para renderizar emails con Jinja2."""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Inicializa el motor de templates.
        
        Args:
            template_dir: Directorio donde están los templates. 
                         Si es None, usa el directorio por defecto.
        """
        if template_dir is None:
            # Usar directorio por defecto relativo a este archivo
            current_dir = Path(__file__).parent
            template_dir = current_dir / "email_templates"
        
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(exist_ok=True)
        
        # Configurar Jinja2
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,  # Para seguridad
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Agregar filtros personalizados
        self._setup_custom_filters()
    
    def _setup_custom_filters(self):
        """Configura filtros personalizados para los templates."""
        
        @self.env.filter
        def money(value):
            """Formatea números como moneda."""
            try:
                return f"${float(value):,.2f}"
            except (ValueError, TypeError):
                return value
        
        @self.env.filter
        def date_format(value, format='%d/%m/%Y'):
            """Formatea fechas."""
            if hasattr(value, 'strftime'):
                return value.strftime(format)
            return value
    
    def render_template(self, template_name: str, **context) -> str:
        """
        Renderiza un template con el contexto dado.
        
        Args:
            template_name: Nombre del archivo template (ej: "orden_completada.html")
            **context: Variables para el template
            
        Returns:
            str: HTML renderizado
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            raise TemplateRenderError(f"Error renderizando template '{template_name}': {str(e)}")
    
    def render_string(self, template_string: str, **context) -> str:
        """
        Renderiza un string template directamente.
        
        Args:
            template_string: String con sintaxis de Jinja2
            **context: Variables para el template
            
        Returns:
            str: String renderizado
        """
        try:
            template = Template(template_string)
            return template.render(**context)
        except Exception as e:
            raise TemplateRenderError(f"Error renderizando string template: {str(e)}")
    
    def list_templates(self) -> list[str]:
        """Lista todos los templates disponibles."""
        if not self.template_dir.exists():
            return []
        
        templates = []
        for file_path in self.template_dir.rglob("*.html"):
            # Obtener ruta relativa al directorio de templates
            relative_path = file_path.relative_to(self.template_dir)
            templates.append(str(relative_path))
        
        return sorted(templates)
    
    def template_exists(self, template_name: str) -> bool:
        """Verifica si un template existe."""
        template_path = self.template_dir / template_name
        return template_path.exists()
    
    def get_template_path(self, template_name: str) -> Path:
        """Obtiene la ruta completa de un template."""
        return self.template_dir / template_name


class TemplateRenderError(Exception):
    """Excepción para errores de renderizado de templates."""
    pass 