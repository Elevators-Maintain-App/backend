from fastapi import APIRouter, Depends, status, HTTPException, Path, Query
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.ordenes_de_trabajo import (
    OrdenDeTrabajoCreate,
    OrdenDeTrabajoUpdate,
    OrdenDeTrabajoCountOut,
    OrdenDeTrabajoSummaryOut,
    OrdenTrabajoListOut,
    OrdenTrabajoDetailOut,
    OrdenDeTrabajoSummarySupervisorOut,
    OrdenDeTrabajoWeeklyComplianceOut,
)
from app.services.ordenes_de_trabajo import OrdenDeTrabajoService
from app.auth.firebase import require_role, get_current_firebase_user

router = APIRouter()

# — ADMIN — #

@router.get("/company/count", response_model=OrdenDeTrabajoCountOut, summary="(admin) Cantidad total")
async def count_company_ordenes(
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    service = OrdenDeTrabajoService(db)
    return {"count": await service.count_by_company(user.company_id)}

@router.get("/company/all", response_model=List[OrdenDeTrabajoSummaryOut], summary="(admin) Listar todas")
async def list_company_ordenes(
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    return await OrdenDeTrabajoService(db).list_summary_by_company(user.company_id)

# — SUPERVISOR — #

@router.get("/supervisor/count", response_model=OrdenDeTrabajoCountOut, summary="(supervisor) Mis totales")
async def count_mis_ordenes(
    user=Depends(get_current_firebase_user),
    db: AsyncSession = Depends(get_db)
):
    if user.role != "superVisor":
        raise HTTPException(status_code=403, detail="No autorizado")
    return {"count": await OrdenDeTrabajoService(db).count_by_supervisor(user.uid)}

# SUPERVISOR: últimas 10
@router.get(
    "/supervisor/all",
    response_model=List[OrdenDeTrabajoSummarySupervisorOut],
    summary="(supervisor) Últimas 10 órdenes asignadas"
)
async def list_mis_ultimas_10(
    user=Depends(get_current_firebase_user),
    db: AsyncSession = Depends(get_db)
):
    if user.role != "superVisor":
        raise HTTPException(403, "No autorizado")
    svc = OrdenDeTrabajoService(db)
    return await svc.list_summary_by_supervisor(user.uid, full=False)

# SUPERVISOR: todas las órdenes
@router.get(
    "/supervisor/all/full",
    response_model=List[OrdenDeTrabajoSummarySupervisorOut],
    summary="(supervisor) Todas mis órdenes asignadas"
)
async def list_mis_todas(
    user=Depends(get_current_firebase_user),
    db: AsyncSession = Depends(get_db)
):
    if user.role != "superVisor":
        raise HTTPException(403, "No autorizado")
    svc = OrdenDeTrabajoService(db)
    return await svc.list_summary_by_supervisor(user.uid, full=True)

@router.get("/supervisor/counts", response_model=dict, summary="(supervisor) Conteos por estado este mes")
async def counts_by_state(
    user=Depends(get_current_firebase_user),
    db: AsyncSession = Depends(get_db)
):
    if user.role != "superVisor":
        raise HTTPException(status_code=403, detail="No autorizado")
    return await OrdenDeTrabajoService(db).counts_by_state_this_month(user.uid, user.company_id)

@router.get("/supervisor/compliance", response_model=OrdenDeTrabajoWeeklyComplianceOut, summary="(supervisor) % Cumplimiento semanal")
async def weekly_compliance(
    user=Depends(get_current_firebase_user),
    db: AsyncSession = Depends(get_db)
):
    if user.role != "superVisor":
        raise HTTPException(status_code=403, detail="No autorizado")
    return await OrdenDeTrabajoService(db).weekly_compliance(user.uid, user.company_id)

# — DETALLE COMPARTIDO — #

@router.get("/{orden_id}", response_model=OrdenTrabajoDetailOut, summary="(admin|superVisor) Detalle")
async def get_orden_detail(
    orden_id: UUID = Path(...),
    user=Depends(get_current_firebase_user),
    db: AsyncSession = Depends(get_db)
):
    return await OrdenDeTrabajoService(db).get_detail(orden_id, user)

# — CREAR (admin ó supervisor) — #

@router.post(
    "/company",
    response_model=OrdenTrabajoDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="(admin | supervisor) Crear una nueva orden"
)
async def create_company_orden(
    orden_in: OrdenDeTrabajoCreate,
    user=Depends(get_current_firebase_user),
    db: AsyncSession = Depends(get_db)
):
    if user.role not in ("admin", "superVisor"):
        raise HTTPException(status_code=403, detail="No autorizado")

    # 1) decidir supervisor_id
    if user.role == "admin":
        if not orden_in.supervisor_id:
            raise HTTPException(status_code=422, detail="supervisor_id obligatorio para admin")
        sup_uid = orden_in.supervisor_id
    else:
        # para supervisor ignoramos cualquier supervisor_id en body
        sup_uid = user.uid

    return await OrdenDeTrabajoService(db).create_for_admin(
        orden_in=orden_in,
        supervisor_id=sup_uid,
        company_id=user.company_id,
        user=user
    )
