from app.api.routes.user_routes import router as user_router
from app.api.routes.item_routes import router as item_router
from app.api.routes.auth import router as auth_router

__all__ = ["user_router", "item_router", "auth_router"] 