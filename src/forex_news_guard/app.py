from fastapi import FastAPI

from forex_news_guard.api.router import api_router
from forex_news_guard.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Alertas para noticias economicas de alto impacto desde Forex Factory.",
    )
    app.include_router(api_router)
    return app
