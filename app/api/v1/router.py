from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.stock import router as stock_router
from app.api.v1.endpoints.movements import router as movements_router
from app.api.v1.endpoints.recipes import router as recipes_router
from app.api.v1.endpoints.sales import router as sales_router
from app.api.v1.endpoints.suppliers import router as suppliers_router
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
from app.api.v1.endpoints.orders import router as orders_router
from app.api.v1.endpoints.invoices import router as invoices_router
from app.api.v1.endpoints.subscriptions import router as subscriptions_router
from app.api.v1.endpoints.notifications import router as notifications_router
from app.api.v1.endpoints.diagnostics import router as diagnostics_router


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
router.include_router(
    table_sessions_router, prefix="/sessions", tags=["Table Sessions"]
)
router.include_router(roles_router, prefix="/roles", tags=["Roles"])
router.include_router(memberships_router, prefix="/memberships", tags=["Memberships"])
router.include_router(stock_router, prefix="/stock", tags=["Stock"])
router.include_router(movements_router, prefix="/movements", tags=["Movements"])
router.include_router(recipes_router, prefix="/recipes", tags=["Recipes"])
router.include_router(sales_router, prefix="/sales", tags=["Sales"])
router.include_router(suppliers_router, prefix="/suppliers", tags=["Suppliers"])
router.include_router(orders_router, prefix="/orders", tags=["Orders"])
router.include_router(invoices_router, prefix="/invoices", tags=["Invoices"])
router.include_router(
    subscriptions_router, prefix="/subscriptions", tags=["Subscriptions"]
)
router.include_router(
    notifications_router, prefix="/notifications", tags=["Notifications"]
)
router.include_router(diagnostics_router, prefix="/diagnostics", tags=["Diagnostics"])
