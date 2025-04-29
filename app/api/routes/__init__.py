from app.api.routes.user_routes import router as user_router
from app.api.routes.item_routes import router as item_router
from app.api.routes.auth import router as auth_router
from app.api.routes.clientes import router as clientes_router
from app.api.routes.tipos_documento import router as tipos_documento_router
from app.api.routes.estados_orden import router as estados_orden_router
from app.api.routes.prioridades import router as prioridades_router
from app.api.routes.tipos_evidencia import router as tipos_evidencia_router
from app.api.routes.tipos_orden import router as tipos_orden_router
from app.api.routes.tipos_unidad import router as tipos_unidad_router
from app.api.routes.proyectos import router as proyectos_router
from app.api.routes.supervisores import router as supervisores_router
from app.api.routes.tecnicos import router as tecnicos_router
from app.api.routes.ordenes_de_trabajo import router as ordenes_trabajo_router
from app.api.routes.checklists import router as checklists_router
from app.api.routes.unidades import router as unidades_router
from app.api.routes.admin_dashboard import router as admin_dashboard
from app.api.routes.dashboard import router as dashboard
from app.api.routes.hojas_de_vida import router as hojas_de_vida
from app.api.routes.zonas_geograficas import router as zonas_geograficas

__all__ = ["user_router", "item_router", "auth_router", "clientes_router", 
           "tipos_documento_router", "estados_orden_router", "prioridades_router", 
           "tipos_evidencia_router", "tipos_orden_router", "tipos_unidad_router", 
           "proyectos_router", "supervisores_router", "tecnicos_router", "ordenes_trabajo_router",
           "checklists_router", "unidades_router", "admin_dashboard", "dashboard",
           "hojas_de_vida", "zonas_geograficas"
           ] 