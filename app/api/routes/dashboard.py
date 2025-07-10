# app/api/routes/dashboard.py
from fastapi import APIRouter, Depends, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.dashboard import DashboardService
from app.auth.firebase import require_role
from app.schemas.dashboard import SuperAdminDashboard, AdminDashboard, SupervisorDashboard, ClienteDashboard, TechnicianDashboard, DashboardTecnicoOut, SuperAdminDashboard
from app.schemas.comunes.shared import DateRangeInput
from app.auth.firebase import get_current_firebase_user
from app.auth.firebase import FirebaseUser
from app.services.orden_trabajo import OrdenTrabajoService

router = APIRouter()

@router.get(
    "/superadmin",
    description="Resumen de usuarios, proyectos, usuarios, planes, etc.",
    dependencies=[Depends(require_role("superAdmin"))],
    response_model=SuperAdminDashboard
)
async def get_super_admin_dashboard(db: AsyncSession = Depends(get_db), current_user: FirebaseUser = Depends(get_current_firebase_user)):
    service = DashboardService(db)
    return await service.get_super_admin_dashboard(current_user)

@router.get(
    "/admin",
    description="Resumen de usuarios, proyectos, usuarios, planes, etc.",
    dependencies=[Depends(require_role("superAdmin", "admin"))],
    response_model=AdminDashboard
)
async def get_admin_dashboard(db: AsyncSession = Depends(get_db), current_user: FirebaseUser = Depends(get_current_firebase_user)):
    service = DashboardService(db)
    return await service.get_admin_dashboard(current_user=current_user)

@router.get(
    "/supervisor",
    description="Resumen de usuarios, proyectos, usuarios, planes, etc.",
    dependencies=[Depends(require_role("superAdmin", "supervisor"))],
    response_model=SupervisorDashboard
)
async def get_supervisor_dashboard(db: AsyncSession = Depends(get_db), current_user: FirebaseUser = Depends(get_current_firebase_user)):
    service = DashboardService(db)
    return await service.get_supervisor_dashboard(current_user)

@router.get(
    "/tecnico",
    description="Resumen de usuarios, proyectos, usuarios, planes, etc.",
    dependencies=[Depends(require_role("superAdmin", "tecnico"))],
    response_model=TechnicianDashboard
)
async def get_tecnico_dashboard(db: AsyncSession = Depends(get_db), current_user: FirebaseUser = Depends(get_current_firebase_user)):
    service = DashboardService(db)
    return await service.get_tecnico_dashboard(current_user)

#Endpoint para el dashboard del tecnico completo

@router.post(
    "/technician",
    response_model=DashboardTecnicoOut,
    summary="Dashboard técnico con métricas y órdenes en curso"
)
async def dashboard_tecnico(
    payload: DateRangeInput = Body(...),
    user=Depends(require_role("technician")),
    db: AsyncSession = Depends(get_db)
):
    return await OrdenTrabajoService(db).get_dashboard_data(
        user.uid, user.company_id, payload.fecha_inicio, payload.fecha_fin
    )


@router.get(
    "/cliente",
    description="Resumen de usuarios, proyectos, usuarios, planes, etc.",
    dependencies=[Depends(require_role("superAdmin", "client"))],
    response_model=ClienteDashboard
)
async def get_cliente_dashboard(db: AsyncSession = Depends(get_db), current_user: FirebaseUser = Depends(get_current_firebase_user)):
    service = DashboardService(db)
    return await service.get_cliente_dashboard(current_user)







# old routes

@router.get("/ordenes-trabajo/resumen", description="Resumen de órdenes de trabajo: abiertas, cerradas, pendientes.")
async def get_resumen_ordenes_trabajo(db: AsyncSession = Depends(get_db)):
    service = DashboardService(db)
    return await service.get_resumen_ordenes_trabajo()

@router.get("/unidades/mantenimiento-pendiente", description="Listar unidades que requieren mantenimiento basado en hoja de vida.")
async def get_unidades_mantenimiento_pendiente(db: AsyncSession = Depends(get_db)):
    service = DashboardService(db)
    return await service.get_unidades_mantenimiento_pendiente()

@router.get("/estadisticas/general", description="Estadísticas generales de operaciones de mantenimiento.")
async def get_estadisticas_generales(db: AsyncSession = Depends(get_db)):
    service = DashboardService(db)
    return await service.get_estadisticas_generales()
