from app.api.routes.clientes import router as clientes_router
from app.api.routes.tipos_documento import router as tipos_documento_router
from app.api.routes.estados_orden import router as estados_orden_router
from app.api.routes.prioridades import router as prioridades_router
from app.api.routes.tipos_evidencia import router as tipos_evidencia_router
from app.api.routes.tipos_orden import router as tipos_orden_router
from app.api.routes.tipos_unidad import router as tipos_unidad_router
from app.api.routes.proyectos import router as proyectos_router
from app.api.routes.ordenes_de_trabajo import router as ordenes_trabajo_router
from app.api.routes.checklists import router as checklists_router
from app.api.routes.unidades import router as unidades_router
from app.api.routes.admin_dashboard import router as admin_dashboard
from app.api.routes.dashboard import router as dashboard
from app.api.routes.hojas_de_vida import router as hojas_de_vida
from app.api.routes.zonas_geograficas import router as zonas_geograficas
from app.api.routes.usuarios import router as usuarios_router
from app.api.routes.compania import router as compania_router
from app.api.routes.lov import router as lov_router
from app.api.routes.nivel_tecnico import router as nivel_tecnico_router
from app.api.routes.ordenes_seguimiento import router as ordenes_seguimiento
from app.api.routes.web_client import router as web_client_router
from app.api.routes.web_superadmin import router as web_superadmin_router

__all__ = ["usuarios_router", "clientes_router", 
           "tipos_documento_router", "estados_orden_router", "prioridades_router", 
           "tipos_evidencia_router", "tipos_orden_router", "tipos_unidad_router", 
           "proyectos_router", "ordenes_trabajo_router",
           "checklists_router", "unidades_router", "admin_dashboard", "dashboard",
           "hojas_de_vida", "zonas_geograficas", "compania_router", "lov_router",
           "nivel_tecnico_router", "ordenes_seguimiento", "web_client_router",
           "web_superadmin_router"
           ] 
