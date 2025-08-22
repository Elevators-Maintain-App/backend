# app/api/routes/ordenes_de_trabajo.py

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from typing import List, Optional
from datetime import date
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.ordenes_de_trabajo import (
    OrdenDeTrabajoCreate,
    OrdenDeTrabajoUpdate,
    OrdenDeTrabajoCountOut,
    OrdenDeTrabajoSummaryOut,
    OrdenDeTrabajoSummarySupervisorOut,
    OrdenDeTrabajoSummaryTechnicianOut,
    OrdenTrabajoDetailOut,
    OrdenDeTrabajoWeeklyComplianceOut,
    OrdenDeTrabajoListOut
)
from app.services.ordenes_de_trabajo import OrdenDeTrabajoService
from app.auth.firebase import require_role, get_current_firebase_user
import logging 

router = APIRouter()

logging.basicConfig(
    level=logging.DEBUG,  # O usa logging.INFO si no necesitas tanto detalle
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
# — ADMIN — #

@router.get(
    "/company/count",
    response_model=OrdenDeTrabajoCountOut,
    summary="(admin) Cantidad total de órdenes"
)
async def count_company_ordenes(
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    return {"count": await OrdenDeTrabajoService(db).count_by_company(user.company_id)}


@router.get(
    "/company/all",
    response_model=List[OrdenDeTrabajoSummaryOut],
    summary="(admin) Listar todas las órdenes"
)
async def list_company_ordenes(
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    return await OrdenDeTrabajoService(db).list_summary_by_company(user.company_id)


# — SUPERVISOR — #

@router.get(
    "/supervisor/count",
    response_model=OrdenDeTrabajoCountOut,
    summary="(supervisor) Mis totales"
)
async def count_mis_ordenes(
    user=Depends(require_role("supervisor")),
    db: AsyncSession = Depends(get_db)
):
    return {"count": await OrdenDeTrabajoService(db).count_by_supervisor(user.uid)}


@router.get(
    "/supervisor/all",
    response_model=List[OrdenDeTrabajoListOut],
    summary="(supervisor) Listar órdenes con filtros"
)
async def list_ordenes_supervisor_filtradas(
    estado_id: Optional[int] = Query(None, description="ID del estado"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio del rango"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin del rango"),
    cliente_id: Optional[str] = Query(None, description="UID del cliente"),
    tecnico_id: Optional[str] = Query(None, description="UID del técnico"),
    proyecto_id: Optional[UUID] = Query(None, description="ID del proyecto"),
    user=Depends(require_role("supervisor")),
    db: AsyncSession = Depends(get_db)
):
    return await OrdenDeTrabajoService(db).list_ordenes_supervisor_filtradas(
        supervisor_uid=user.uid,
        estado_id=estado_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        cliente_id=cliente_id,
        tecnico_id=tecnico_id,
        proyecto_id=proyecto_id
    )


@router.get(
    "/supervisor/all/full",
    response_model=List[OrdenDeTrabajoSummarySupervisorOut],
    summary="(supervisor) Todas mis órdenes"
)
async def list_mis_todas(
    user=Depends(require_role("supervisor")),
    db: AsyncSession = Depends(get_db)
):
    return await OrdenDeTrabajoService(db).list_summary_by_supervisor(user.uid, full=True)


@router.get(
    "/supervisor/counts",
    response_model=dict,
    summary="(supervisor) Conteos por estado (mes)"
)
async def counts_by_state_supervisor(
    user=Depends(require_role("supervisor")),
    db: AsyncSession = Depends(get_db)
):
    return await OrdenDeTrabajoService(db).counts_by_state_this_month(user.uid, user.company_id)


@router.get(
    "/supervisor/compliance",
    response_model=OrdenDeTrabajoWeeklyComplianceOut,
    summary="(supervisor) % Cumplimiento (mes)"
)
async def monthly_compliance_supervisor(
    user=Depends(require_role("supervisor")),
    db: AsyncSession = Depends(get_db)
):
    return await OrdenDeTrabajoService(db).monthly_compliance(user.uid, user.company_id)


# — TÉCNICO — #

@router.get(
    "/technician/count",
    response_model=OrdenDeTrabajoCountOut,
    summary="(technician) Mis totales (mes)"
)
async def count_mis_ordenes_tec(
    user=Depends(require_role("technician")),
    db: AsyncSession = Depends(get_db)
):
    return {"count": await OrdenDeTrabajoService(db).count_by_technician(user.uid)}


@router.get(
    "/technician/all",
    response_model=List[OrdenDeTrabajoSummaryTechnicianOut],
    summary="(technician) Últimas 10 órdenes"
)
async def list_mis_ultimas_10_tec(
    user=Depends(require_role("technician")),
    db: AsyncSession = Depends(get_db)
):
    return await OrdenDeTrabajoService(db).list_summary_by_technician(user.uid, full=False)


@router.get(
    "/technician/all/full",
    response_model=List[OrdenDeTrabajoSummaryTechnicianOut],
    summary="(technician) Todas mis órdenes"
)
async def list_mis_todas_tec(
    user=Depends(require_role("technician")),
    db: AsyncSession = Depends(get_db)
):
    return await OrdenDeTrabajoService(db).list_summary_by_technician(user.uid, full=True)


@router.get(
    "/technician/counts",
    response_model=dict,
    summary="(technician) Conteos por estado (mes)"
)
async def counts_by_state_tec(
    user=Depends(require_role("technician")),
    db: AsyncSession = Depends(get_db)
):
    return await OrdenDeTrabajoService(db).counts_by_state_this_month_technician(user.uid, user.company_id)


@router.get(
    "/technician/compliance",
    response_model=OrdenDeTrabajoWeeklyComplianceOut,
    summary="(technician) % Cumplimiento (mes)"
)
async def monthly_compliance_tec(
    user=Depends(require_role("technician")),
    db: AsyncSession = Depends(get_db)
):
    return await OrdenDeTrabajoService(db).monthly_compliance_technician(user.uid, user.company_id)


# — DETALLE COMPARTIDO — #

@router.get(
    "/{orden_id}",
    response_model=OrdenTrabajoDetailOut,
    summary="(admin|supervisor|technician) Detalle de orden"
)
async def get_orden_detail(
    orden_id: UUID = Path(...),
    user=Depends(get_current_firebase_user),
    db: AsyncSession = Depends(get_db)
):
    return await OrdenDeTrabajoService(db).get_detail(orden_id, user)


# — CREAR (admin o supervisor) — #

@router.post(
    "/",
    response_model=OrdenTrabajoDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="(admin/supervisor) Crear orden"
)
async def create_company_orden(
    orden_in: OrdenDeTrabajoCreate,
    user = Depends(require_role("admin", "supervisor")),
    db: AsyncSession = Depends(get_db)
):
    return await OrdenDeTrabajoService(db).create(
        orden_in=orden_in,
        company_id=user.company_id,
        user=user
    )
