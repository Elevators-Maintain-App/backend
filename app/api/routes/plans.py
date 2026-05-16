from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.firebase import FirebaseUser, require_role
from app.db.session import get_db
from app.schemas.subscriptions import AdminPlanRead
from app.services.plans import SubscriptionStatusService


router = APIRouter()


@router.get(
    "/admin/plans",
    response_model=list[AdminPlanRead],
)
async def list_admin_plans(
    include_inactive: bool = Query(False),
    _user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> list[AdminPlanRead]:
    return await SubscriptionStatusService(db).list_plans(include_inactive=include_inactive)
