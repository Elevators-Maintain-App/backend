"""
Procesador de templates para optimizar emails.
"""

import re
from typing import Optional
from pathlib import Path

try:
    from premailer import Premailer
    PREMAILER_AVAILABLE = True
except ImportError:
    PREMAILER_AVAILABLE = False


class TemplateProcessor:
    """Procesador para optimizar templates de email."""
    
    def __init__(self, use_premailer: bool = True):
        """
        Inicializa el procesador.
        
        Args:
            use_premailer: Si usar Premailer para CSS inline (requiere pip install premailer)
        """
        self.use_premailer = use_premailer and PREMAILER_AVAILABLE
        
        if use_premailer and not PREMAILER_AVAILABLE:
            print("⚠️  Premailer no está instalado. Usa: pip install premailer")
            print("   CSS inline no estará disponible.")
    
    def process_email_html(self, html: str, css_file: Optional[str] = None) -> str:
        """
        Procesa HTML para email: CSS inline, optimizaciones, etc.
        
        Args:
            html: HTML del email
            css_file: Ruta a archivo CSS externo (opcional)
            
        Returns:
            str: HTML optimizado para email
        """
        # Si hay archivo CSS, incluirlo en el HTML
        if css_file and Path(css_file).exists():
            html = self._include_css_file(html, css_file)
        
        # Convertir CSS a inline si Premailer está disponible
        if self.use_premailer:
            html = self._css_to_inline(html)
        
        # Optimizaciones específicas para email
        html = self._optimize_for_email(html)
        
        return html
    
    def _include_css_file(self, html: str, css_file: str) -> str:
        """Incluye CSS externo en el HTML."""
        try:
            with open(css_file, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            # Buscar si ya hay un tag <style> en el head
            if '<style>' in html or '<style ' in html:
                # Agregar al final del último style
                html = html.replace('</style>', f'\n{css_content}\n</style>', 1)
            else:
                # Agregar nuevo tag style en el head
                if '</head>' in html:
                    style_tag = f'<style type="text/css">\n{css_content}\n</style>\n</head>'
                    html = html.replace('</head>', style_tag)
                else:
                    # Si no hay head, agregarlo al inicio
                    style_tag = f'<style type="text/css">\n{css_content}\n</style>\n'
                    html = style_tag + html
                    
        except Exception as e:
            print(f"⚠️  Error incluyendo CSS file {css_file}: {e}")
        
        return html
    
    def _css_to_inline(self, html: str) -> str:
        """Convierte CSS a inline usando Premailer."""
        try:
            p = Premailer(
                html=html,
                base_path=None,
                preserve_internal_links=True,
                keep_style_tags=True,
                include_star_selectors=True,
                remove_classes=False,
                strip_important=False,
                external_encoding='utf-8'
            )
            return p.transform()
        except Exception as e:
            print(f"⚠️  Error convirtiendo CSS a inline: {e}")
            return html
    
    def _optimize_for_email(self, html: str) -> str:
        """Aplicar optimizaciones específicas para clients de email."""
        
        # Asegurar que las tablas tengan border="0" y cellpadding="0" cellspacing="0"
        html = re.sub(
            r'<table(?!\s[^>]*border=)',
            '<table border="0" cellpadding="0" cellspacing="0"',
            html
        )
        
        # Agregar display:block a imágenes para evitar espacios
        html = re.sub(
            r'<img(?![^>]*style=)',
            '<img style="display:block"',
            html
        )
        
        # Asegurar que links tengan color específico (algunos clients los cambian)
        html = re.sub(
            r'<a(?![^>]*style=.*color)',
            '<a style="color: #007bff; text-decoration: none"',
            html
        )
        
        return html
    
    def create_base_template(self, title: str = "Email") -> str:
        """
        Crea un template base optimizado para email.
        
        Args:
            title: Título del email
            
        Returns:
            str: Template base HTML
        """
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{title}</title>
    <style type="text/css">
        /* Reset básico para email */
        body, table, td, p, a, li, blockquote {{
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
        }}
        
        table, td {{
            mso-table-lspace: 0pt;
            mso-table-rspace: 0pt;
        }}
        
        img {{
            -ms-interpolation-mode: bicubic;
            border: 0;
            outline: none;
            text-decoration: none;
            display: block;
        }}
        
        body {{
            margin: 0 !important;
            padding: 0 !important;
            background-color: #f4f4f4;
            font-family: Arial, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: #333333;
        }}
        
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
        }}
        
        .header {{
            background-color: #2c3e50;
            color: #ffffff;
            padding: 20px;
            text-align: center;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #6c757d;
        }}
        
        .btn {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #007bff;
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
        }}
        
        .btn:hover {{
            background-color: #0056b3;
        }}
        
        .alert {{
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }}
        
        .alert-success {{
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }}
        
        .alert-warning {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
        }}
        
        .alert-danger {{
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }}
        
        /* Responsive */
        @media screen and (max-width: 600px) {{
            .email-container {{
                width: 100% !important;
                max-width: 100% !important;
            }}
            
            .content {{
                padding: 20px !important;
            }}
        }}
    </style>
</head>
<body>
    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
        <tr>
            <td>
                <div class="email-container">
                    
                    <!-- Content -->
                    <div class="content">
                        {{{{ content }}}}
                    </div>
                    
                    <!-- Footer -->
                    <div class="footer">
                        <p style="margin: 0;">
                            {{{{ empresa_nombre or "Hazard Service" }}}} - {{{{ year or "2024" }}}}<br>
                            {{{{ empresa_direccion or "Dirección de la empresa" }}}}
                        </p>
                        <p style="margin: 10px 0 0 0;">
                            Si tienes preguntas, contacta: {{{{ soporte_email or "soporte@hazard.com" }}}}
                        </p>
                    </div>
                </div>
            </td>
        </tr>
    </table>
</body>
</html>""" 