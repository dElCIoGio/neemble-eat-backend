from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.user import router as user_router
from app.api.v1.endpoints.restaurants import router as analysis_router
from app.api.v1.endpoints.invitation import router as invitation_router
from app.api.v1.endpoints.blog import router as blog_router
from app.api.v1.endpoints.bookings import router as booking_router
from app.api.v1.endpoints.insights import router as insights_router
from app.api.v1.endpoints.items import router as items_router
from app.api.v1.endpoints.menus import router as menus_router
from app.api.v1.endpoints.categories import router as categories_router
from app.api.v1.endpoints.tables import router as tables_router
from app.api.v1.endpoints.table_sessions import router as table_sessions_router
from app.api.v1.endpoints.roles import router as roles_router
from app.api.v1.endpoints.memberships import router as memberships_router


router = APIRouter()


router.include_router(blog_router, prefix="/blog", tags=["Blog"])
router.include_router(invitation_router, prefix="/invitations", tags=["Invitation"])
router.include_router(user_router, prefix="/users", tags=["User"])
router.include_router(analysis_router, prefix="/restaurants", tags=["Restaurant"])
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
router.include_router(booking_router, prefix="/bookings", tags=["Bookings"])
router.include_router(insights_router, prefix="/insights", tags=["AI Insights"])
router.include_router(items_router, prefix="/items", tags=["Items"])
router.include_router(menus_router, prefix="/menus", tags=["Menus"])
router.include_router(categories_router, prefix="/categories", tags=["Categories"])
router.include_router(tables_router, prefix="/tables", tags=["Tables"])
router.include_router(table_sessions_router, prefix="/sessions", tags=["Table Sessions"])
router.include_router(roles_router, prefix="/roles", tags=["Roles"])
router.include_router(memberships_router, prefix="/memberships", tags=["Memberships"])
