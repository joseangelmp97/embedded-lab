from sqlalchemy import create_engine, func, select, text
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
    INITIAL_PATH_MODULES,
    LAB_MODULE_ASSIGNMENTS,
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
        assert len(LAB_MODULE_ASSIGNMENTS) == len(INITIAL_LABS)

        path_id_by_name = {path.name: path.id for path in all_paths}
        for lab_id, path_name in LAB_PATH_ASSIGNMENTS.items():
            assert all_labs[lab_id].path_id == path_id_by_name[path_name]

        modules_by_id = {module["id"]: module for module in INITIAL_PATH_MODULES}
        for module_id in modules_by_id:
            module_labs = sorted(
                [lab for lab in all_labs.values() if lab.module_id == module_id],
                key=lambda row: row.order_index,
            )
            assert module_labs
            assert module_labs[0].prerequisite_lab_id is None

            for current_lab, previous_lab in zip(module_labs[1:], module_labs[:-1], strict=False):
                assert current_lab.prerequisite_lab_id == previous_lab.id
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

        pwm_lab = db.scalar(select(Lab).where(Lab.id == "gpio-led-basics"))
        assert pwm_lab is not None
        pwm_lab.path_id = "fcb79cb6-18f6-4347-a7cb-f8f57c4d4f17"
        pwm_lab.prerequisite_lab_id = "digital-logic-voltage-levels"
        db.commit()

        with pytest.raises(ValueError, match="same path"):
            validate_module_prerequisite_integrity(db=db)
    finally:
        db.close()
        engine.dispose()


def test_seed_counts_and_ordering_match_catalog_v2(tmp_path):
    db_file = tmp_path / "path_counts_ordering.db"
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

        all_labs = list(db.scalars(select(Lab).order_by(Lab.order_index.asc())))
        assert len(all_labs) == 30
        assert [lab.order_index for lab in all_labs] == list(range(1, 31))
        assert len(INITIAL_PATH_MODULES) == 5

        expected_module_names = {
            "Embedded Foundations",
            "MCU Core",
            "Interfaces and Communication",
            "Sensors and Actuators",
            "Reliability and Debugging",
        }
        assert {module["title"] for module in INITIAL_PATH_MODULES} == expected_module_names
    finally:
        db.close()
        engine.dispose()


def test_seed_payloads_include_required_lab_fields_and_upsert_restores_drift(tmp_path):
    required_fields = {
        "id",
        "slug",
        "title",
        "description",
        "difficulty",
        "estimated_minutes",
        "status",
        "order_index",
        "learning_objectives_json",
        "tags_json",
        "hardware_requirements_json",
        "content_version",
        "is_optional",
    }

    for payload in INITIAL_LABS:
        assert required_fields.issubset(payload.keys())

    db_file = tmp_path / "seed_upsert_restore.db"
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
        seed_initial_labs(db=db)

        changed_lab = db.scalar(select(Lab).where(Lab.id == "gpio-led-basics"))
        assert changed_lab is not None
        changed_lab.title = "WRONG TITLE"
        db.commit()

        seed_initial_labs(db=db)
        restored_lab = db.scalar(select(Lab).where(Lab.id == "gpio-led-basics"))
        assert restored_lab is not None
        assert restored_lab.title == "GPIO and LED basics"
        assert db.scalar(select(func.count()).select_from(Lab)) == len(INITIAL_LABS)
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
