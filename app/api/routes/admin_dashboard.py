# app/api/routes/admin_dashboard.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.admin_dashboard import AdminDashboardService

router = APIRouter()

@router.get("/usuarios", description="Listar todos los usuarios registrados en el sistema.")
async def get_usuarios(db: AsyncSession = Depends(get_db)):
    service = AdminDashboardService(db)
    return await service.get_usuarios()

@router.get("/estadisticas/usuarios", description="Obtener estadísticas de usuarios: cantidad de técnicos, supervisores y clientes.")
async def get_estadisticas_usuarios(db: AsyncSession = Depends(get_db)):
    service = AdminDashboardService(db)
    return await service.get_estadisticas_usuarios()
