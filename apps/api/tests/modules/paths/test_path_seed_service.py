from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker
import pytest

from app.modules.labs.models.lab import Lab
from app.modules.labs.services.lab_service import INITIAL_LABS, seed_initial_labs
from app.modules.paths.models.path import Path
from app.modules.paths.services.path_service import (
    INITIAL_PATHS,
    LAB_PATH_ASSIGNMENTS,
    assign_labs_to_paths,
    seed_initial_paths,
)
from app.modules.paths.services.path_module_service import (
    assign_labs_to_modules,
    seed_initial_path_modules,
    validate_module_prerequisite_integrity,
)
from app.shared.db.base import Base


def test_seed_initial_paths_is_idempotent_and_assigns_labs(tmp_path):
    db_file = tmp_path / "path_seed_service.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=engine)

    db = testing_session_local()
    try:
        seed_initial_paths(db=db)
        seed_initial_paths(db=db)
        seed_initial_path_modules(db=db)
        seed_initial_path_modules(db=db)

        seed_initial_labs(db=db)
        assign_labs_to_paths(db=db)
        assign_labs_to_paths(db=db)
        assign_labs_to_modules(db=db)
        assign_labs_to_modules(db=db)
        validate_module_prerequisite_integrity(db=db)

        all_paths = list(db.scalars(select(Path).order_by(Path.order.asc())))
        all_labs = {lab.id: lab for lab in db.scalars(select(Lab)).all()}

        assert len(all_paths) == len(INITIAL_PATHS)
        assert [path.name for path in all_paths] == [path_payload["name"] for path_payload in INITIAL_PATHS]
        assert len(all_labs) == len(INITIAL_LABS)

        path_id_by_name = {path.name: path.id for path in all_paths}
        for lab_id, path_name in LAB_PATH_ASSIGNMENTS.items():
            assert all_labs[lab_id].path_id == path_id_by_name[path_name]

        sensors_labs = [
            lab
            for lab in sorted(all_labs.values(), key=lambda row: row.order_index)
            if lab.path_id == path_id_by_name["Sensors & IO"]
        ]
        assert len(sensors_labs) == 2
        assert sensors_labs[0].prerequisite_lab_id is None
        assert sensors_labs[1].prerequisite_lab_id == sensors_labs[0].id
    finally:
        db.close()
        engine.dispose()


def test_validate_module_prerequisite_integrity_rejects_cross_path_prerequisite(tmp_path):
    db_file = tmp_path / "path_integrity.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=engine)

    db = testing_session_local()
    try:
        seed_initial_paths(db=db)
        seed_initial_path_modules(db=db)
        seed_initial_labs(db=db)
        assign_labs_to_paths(db=db)
        assign_labs_to_modules(db=db)

        pwm_lab = db.scalar(select(Lab).where(Lab.id == "pwm-motor-speed-control"))
        assert pwm_lab is not None
        pwm_lab.prerequisite_lab_id = "gpio-led-basics"
        db.commit()

        with pytest.raises(ValueError, match="same path"):
            validate_module_prerequisite_integrity(db=db)
    finally:
        db.close()
        engine.dispose()


def test_assign_labs_to_paths_is_safe_for_legacy_sqlite_schema(tmp_path):
    db_file = tmp_path / "legacy_paths_schema.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE paths (id VARCHAR(36) PRIMARY KEY, name VARCHAR(255) NOT NULL)"))
        connection.execute(
            text(
                "CREATE TABLE labs (id VARCHAR(100) PRIMARY KEY, title VARCHAR(255) NOT NULL, order_index INTEGER NOT NULL)"
            )
        )

    db = testing_session_local()
    try:
        assign_labs_to_paths(db=db)
    finally:
        db.close()
        engine.dispose()
