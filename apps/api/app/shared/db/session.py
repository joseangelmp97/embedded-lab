from sqlalchemy import create_engine, inspect, text
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

    inspector = inspect(engine)
    if "labs" not in inspector.get_table_names():
        return

    lab_columns = {column["name"] for column in inspector.get_columns("labs")}
    if "prerequisite_lab_id" in lab_columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE labs ADD COLUMN prerequisite_lab_id VARCHAR(100)"))
