from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.shared.config.settings import get_settings


settings = get_settings()

engine_kwargs: dict[str, object] = {"pool_pre_ping": True}

if settings.database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **engine_kwargs)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def init_db() -> None:
    from app.shared.db.models import Base

    Base.metadata.create_all(bind=engine)
