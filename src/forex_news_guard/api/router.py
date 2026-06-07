from fastapi import APIRouter

from forex_news_guard.api.routes.alerts import router as alerts_router
from forex_news_guard.api.routes.events import router as events_router
from forex_news_guard.api.routes.health import router as health_router
from forex_news_guard.api.routes.settings import router as settings_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(alerts_router, prefix="/api/v1/alerts", tags=["alerts"])
api_router.include_router(settings_router, prefix="/api/v1/settings", tags=["settings"])
api_router.include_router(events_router, prefix="/api/v1/events", tags=["events"])
