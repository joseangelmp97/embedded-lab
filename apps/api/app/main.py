from fastapi import FastAPI

from app.api.router import api_router
from app.shared.config.settings import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.app_debug,
)

app.include_router(api_router)
