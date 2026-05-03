from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi.middleware.cors import CORSMiddleware

# Initialize Firebase before importing routes that use Firebase services
from app.config import firebase_config

from app.api.routes import (
    admin_dashboard,
    checklists_router,
    clientes_router,
    compania_router,
    dashboard,
    estados_orden_router,
    hojas_de_vida,
    lov_router,
    nivel_tecnico_router,
    ordenes_seguimiento,
    ordenes_trabajo_router,
    prioridades_router,
    proyectos_router,
    tipos_documento_router,
    tipos_evidencia_router,
    tipos_orden_router,
    tipos_unidad_router,
    unidades_router,
    usuarios_router,
    zonas_geograficas
)
from app.core.config import settings
from app.db.session import engine, Base
from app.core.openapi_config import OpenAPIConfig
from app.middleware.observability import observability_middleware

# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    async with engine.begin() as conn:
        # In production, use Alembic for migrations instead
        if settings.environment == "development":
            await conn.run_sync(Base.metadata.create_all)
    
    print("Application startup complete")
    yield
    # Shutdown: Cleanup resources
    print("Application shutdown complete")

# Create FastAPI application with JWT security
app = FastAPI(
    title=settings.app_name,
    description="VertiOne API v1",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    debug=settings.debug
    
)

app.middleware("http")(observability_middleware)

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.get("/", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "Ok", "message": "API is running"}

# Register API routes
app.include_router(admin_dashboard, prefix="/api/dashboard", tags=["Admin Dashboard"])
app.include_router(checklists_router, prefix="/api/checklists", tags=["Checklists"])
app.include_router(clientes_router, prefix="/api/clientes", tags=["Clientes"])
app.include_router(compania_router, prefix="/api/companias", tags=["Companias"])
app.include_router(dashboard, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(estados_orden_router, prefix="/api/estados-orden", tags=["Enums"])
app.include_router(hojas_de_vida, prefix="/api/hojas-vida", tags=["Hojas de Vida"])
app.include_router(lov_router, prefix="/api/lov", tags=["LOV"])
app.include_router(nivel_tecnico_router, prefix="/api/niveles-tecnicos", tags=["Niveles Tecnicos"])
app.include_router(ordenes_seguimiento, prefix="/api/seguimiento", tags=["Seguimiento"])
app.include_router(ordenes_trabajo_router, prefix="/api/ordenes-trabajo", tags=["Ordenes de Trabajo"])
app.include_router(prioridades_router, prefix="/api/prioridades", tags=["Enums"])
app.include_router(proyectos_router, prefix="/api/proyectos", tags=["Proyectos"])
app.include_router(tipos_documento_router, prefix="/api/tipos-documento", tags=["Enums"])
app.include_router(tipos_evidencia_router, prefix="/api/tipos-evidencia", tags=["Enums"])
app.include_router(tipos_orden_router, prefix="/api/tipos-orden", tags=["Enums"])
app.include_router(tipos_unidad_router, prefix="/api/tipos-unidad", tags=["Enums"])
app.include_router(unidades_router, prefix="/api/unidades", tags=["Unidades"])
app.include_router(usuarios_router, prefix="/api/usuarios", tags=["Usuarios"])
app.include_router(zonas_geograficas, prefix="/api/zonas-geograficas", tags=["Zonas Geograficas"])

# add openapi config
openapi_config = OpenAPIConfig(app)
app.openapi = openapi_config.get_openapi


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True) 
