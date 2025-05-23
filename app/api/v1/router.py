from fastapi import APIRouter

from app.api.v1.endpoint.auth import router as auth_router
from app.api.v1.endpoint.analytics import router as analytics_router
from app.api.v1.endpoint.user import router as user_router
from app.api.v1.endpoint.restaurants import router as analysis_router
from app.api.v1.endpoint.invitation import router as invitation_router
from app.api.v1.endpoint.blog import router as blog_router


router = APIRouter()


router.include_router(blog_router, prefix="/blog", tags=["Blog"])
router.include_router(invitation_router, prefix="/invitations", tags=["Invitation"])
router.include_router(user_router, prefix="/users", tags=["User"])
router.include_router(analysis_router, prefix="/restaurants", tags=["Restaurant"])
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
