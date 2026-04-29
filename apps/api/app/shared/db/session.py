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

    missing_column_statements: list[str] = []
    if "prerequisite_lab_id" not in lab_columns:
        missing_column_statements.append("ALTER TABLE labs ADD COLUMN prerequisite_lab_id VARCHAR(100)")
    if "module_id" not in lab_columns:
        missing_column_statements.append("ALTER TABLE labs ADD COLUMN module_id VARCHAR(36)")
    if "slug" not in lab_columns:
        missing_column_statements.append("ALTER TABLE labs ADD COLUMN slug VARCHAR(255)")
    if "learning_objectives_json" not in lab_columns:
        missing_column_statements.append("ALTER TABLE labs ADD COLUMN learning_objectives_json VARCHAR")
    if "tags_json" not in lab_columns:
        missing_column_statements.append("ALTER TABLE labs ADD COLUMN tags_json VARCHAR")
    if "hardware_requirements_json" not in lab_columns:
        missing_column_statements.append("ALTER TABLE labs ADD COLUMN hardware_requirements_json VARCHAR")
    if "content_version" not in lab_columns:
        missing_column_statements.append("ALTER TABLE labs ADD COLUMN content_version INTEGER NOT NULL DEFAULT 1")
    if "is_optional" not in lab_columns:
        missing_column_statements.append("ALTER TABLE labs ADD COLUMN is_optional BOOLEAN NOT NULL DEFAULT 0")

    if not missing_column_statements:
        return

    with engine.begin() as connection:
        for statement in missing_column_statements:
            connection.execute(text(statement))
