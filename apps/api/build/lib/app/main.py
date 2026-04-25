from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.shared.config.settings import get_settings
from app.shared.db.session import init_db


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.app_debug,
    lifespan=lifespan,
)

app.include_router(api_router)
