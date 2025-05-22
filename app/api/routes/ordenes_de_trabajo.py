# app/api/routes/ordenes_de_trabajo.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas.ordenes_de_trabajo import OrdenDeTrabajoCreate, OrdenDeTrabajoUpdate, OrdenDeTrabajoInDBBase
from app.services.ordenes_de_trabajo import OrdenDeTrabajoService
from app.auth.firebase import get_current_firebase_user

router = APIRouter()

@router.get("/supervisor", response_model=List[OrdenDeTrabajoInDBBase])
async def listar_ordenes_supervisor(user=Depends(get_current_firebase_user), db=Depends(get_db)):
    service = OrdenDeTrabajoService(db)
    return await service.listar_por_supervisor(user.uid)

@router.post("/supervisor", response_model=OrdenDeTrabajoInDBBase, status_code=201)
async def crear_orden_supervisor(
    orden_in: OrdenDeTrabajoCreate,
    user=Depends(get_current_firebase_user),
    db=Depends(get_db)
):
    service = OrdenDeTrabajoService(db)
    return await service.crear_para_supervisor(
        orden_in,
        supervisor_uid=user.uid,
        company_id=user.company_id
    )

@router.get("/", response_model=List[OrdenDeTrabajoInDBBase])
async def get_ordenes_trabajo(db: AsyncSession = Depends(get_db)):
    service = OrdenDeTrabajoService(db)
    return await service.get_all()

@router.get("/{orden_id}", response_model=OrdenDeTrabajoInDBBase)
async def get_orden_trabajo(orden_id: UUID, db: AsyncSession = Depends(get_db)):
    service = OrdenDeTrabajoService(db)
    return await service.get_by_id(orden_id)

@router.post("/", response_model=OrdenDeTrabajoInDBBase, status_code=status.HTTP_201_CREATED)
async def create_orden_trabajo(orden_in: OrdenDeTrabajoCreate, db: AsyncSession = Depends(get_db)):
    service = OrdenDeTrabajoService(db)
    return await service.create(orden_in)

@router.put("/{orden_id}", response_model=OrdenDeTrabajoInDBBase)
async def update_orden_trabajo(orden_id: UUID, orden_in: OrdenDeTrabajoUpdate, db: AsyncSession = Depends(get_db)):
    service = OrdenDeTrabajoService(db)
    return await service.update(orden_id, orden_in)

@router.delete("/{orden_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_orden_trabajo(orden_id: UUID, db: AsyncSession = Depends(get_db)):
    service = OrdenDeTrabajoService(db)
    await service.delete(orden_id)

