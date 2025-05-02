# app/api/routes/dashboard.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.dashboard import DashboardService

router = APIRouter()


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
