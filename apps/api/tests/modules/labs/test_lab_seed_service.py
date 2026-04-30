from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.modules.labs.models.exercise import Exercise
from app.modules.labs.services.lab_service import INITIAL_INTERACTIVE_EXERCISES, seed_initial_labs
from app.shared.db.base import Base


def test_seed_initial_labs_creates_only_expected_phase8_interactive_exercises(tmp_path):
    db_file = tmp_path / "labs_seed.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    db = session_local()
    try:
        seed_initial_labs(db=db)

        seeded = list(db.scalars(select(Exercise).order_by(Exercise.lab_id.asc(), Exercise.order_index.asc(), Exercise.id.asc())))
        expected_ids = {item["id"] for item in INITIAL_INTERACTIVE_EXERCISES}
        expected_labs = {"digital-logic-voltage-levels", "gpio-led-basics", "timer-periodic-tasks"}

        assert len(seeded) == len(INITIAL_INTERACTIVE_EXERCISES)
        assert {item.id for item in seeded} == expected_ids
        assert {item.lab_id for item in seeded} == expected_labs
        assert all(item.status == "published" for item in seeded)
        assert all(item.content_version == 1 for item in seeded)
    finally:
        db.close()
        engine.dispose()


def test_seed_initial_labs_is_idempotent_for_phase8_exercises(tmp_path):
    db_file = tmp_path / "labs_seed_idempotent.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    db = session_local()
    try:
        seed_initial_labs(db=db)
        first_snapshot = list(db.scalars(select(Exercise).order_by(Exercise.id.asc())))

        seed_initial_labs(db=db)
        second_snapshot = list(db.scalars(select(Exercise).order_by(Exercise.id.asc())))

        assert len(first_snapshot) == len(second_snapshot) == len(INITIAL_INTERACTIVE_EXERCISES)
        assert [item.id for item in first_snapshot] == [item.id for item in second_snapshot]
    finally:
        db.close()
        engine.dispose()
