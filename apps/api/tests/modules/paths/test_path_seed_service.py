from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.modules.labs.models.lab import Lab
from app.modules.labs.services.lab_service import INITIAL_LABS, seed_initial_labs
from app.modules.paths.models.path import Path
from app.modules.paths.services.path_service import (
    INITIAL_PATHS,
    LAB_PATH_ASSIGNMENTS,
    assign_labs_to_paths,
    seed_initial_paths,
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

        seed_initial_labs(db=db)
        assign_labs_to_paths(db=db)
        assign_labs_to_paths(db=db)

        all_paths = list(db.scalars(select(Path).order_by(Path.order.asc())))
        all_labs = {lab.id: lab for lab in db.scalars(select(Lab)).all()}

        assert len(all_paths) == len(INITIAL_PATHS)
        assert [path.name for path in all_paths] == [path_payload["name"] for path_payload in INITIAL_PATHS]
        assert len(all_labs) == len(INITIAL_LABS)

        path_id_by_name = {path.name: path.id for path in all_paths}
        for lab_id, path_name in LAB_PATH_ASSIGNMENTS.items():
            assert all_labs[lab_id].path_id == path_id_by_name[path_name]
    finally:
        db.close()
        engine.dispose()
