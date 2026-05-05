from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.firebase import FirebaseUser, require_role
from app.db.session import get_db
from app.schemas.web_client import WebClientDashboard
from app.services.web.client_dashboard_service import WebClientDashboardService


router = APIRouter()


@router.get("/dashboard", response_model=WebClientDashboard)
async def get_client_dashboard(
    current_user: FirebaseUser = Depends(require_role("client")),
    db: AsyncSession = Depends(get_db),
) -> WebClientDashboard:
    return await WebClientDashboardService(db).get_dashboard(current_user)
