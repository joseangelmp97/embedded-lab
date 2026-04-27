from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.modules.labs.services.lab_service import seed_initial_labs
from app.modules.paths.services.path_service import assign_labs_to_paths, seed_initial_paths
from app.shared.config.settings import get_settings
from app.shared.db.session import SessionLocal, init_db


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_initial_paths(db=db)
        seed_initial_labs(db=db)
        assign_labs_to_paths(db=db)
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.app_debug,
    lifespan=lifespan,
)

app.include_router(api_router)
