# app/api/routes/supervisores.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas.supervisores import SupervisorCreate, SupervisorUpdate, SupervisorInDBBase, DashboardSupervisorOut
from app.schemas.ordenes_de_trabajo import OrdenDeTrabajoInDBBase
from app.services.supervisores import SupervisorService

router = APIRouter()

# Rutas CRUD normales
@router.get("/", response_model=List[SupervisorInDBBase])
async def get_supervisores(db: AsyncSession = Depends(get_db)):
    service = SupervisorService(db)
    return await service.get_all()

@router.get("/{supervisor_id}", response_model=SupervisorInDBBase)
async def get_supervisor(supervisor_id: UUID, db: AsyncSession = Depends(get_db)):
    service = SupervisorService(db)
    return await service.get_by_id(supervisor_id)

@router.post("/", response_model=SupervisorInDBBase, status_code=status.HTTP_201_CREATED)
async def create_supervisor(supervisor_in: SupervisorCreate, db: AsyncSession = Depends(get_db)):
    service = SupervisorService(db)
    return await service.create(supervisor_in)

@router.put("/{supervisor_id}", response_model=SupervisorInDBBase)
async def update_supervisor(supervisor_id: UUID, supervisor_in: SupervisorUpdate, db: AsyncSession = Depends(get_db)):
    service = SupervisorService(db)
    return await service.update(supervisor_id, supervisor_in)

@router.delete("/{supervisor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supervisor(supervisor_id: UUID, db: AsyncSession = Depends(get_db)):
    service = SupervisorService(db)
    await service.delete(supervisor_id)

# Rutas Especiales 

@router.get("/{supervisor_id}/ordenes-trabajo", response_model=List[OrdenDeTrabajoInDBBase], description="Listar todas las órdenes de trabajo supervisadas por un supervisor.")
async def get_ordenes_supervisor(supervisor_id: UUID, skip: int = Query(0, ge=0), limit: int = Query(10, gt=0), db: AsyncSession = Depends(get_db)):
    service = SupervisorService(db)
    return await service.get_ordenes_trabajo(supervisor_id, skip=skip, limit=limit)

# NUEVA RUTA: Dashboard supervisor
@router.get("/{supervisor_id}/dashboard", response_model=DashboardSupervisorOut, description="Dashboard de supervisor con KPIs y órdenes recientes.")
async def get_dashboard_supervisor(supervisor_id: UUID, db: AsyncSession = Depends(get_db)):
    service = SupervisorService(db)
    return await service.get_dashboard(supervisor_id)
