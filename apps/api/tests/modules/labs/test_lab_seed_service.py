from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.modules.labs.models.exercise import Exercise
from app.modules.labs.services.lab_service import INITIAL_INTERACTIVE_EXERCISES, INITIAL_LABS, seed_initial_labs
from app.shared.db.base import Base


def test_seed_initial_labs_creates_expected_interactive_exercises(tmp_path):
    db_file = tmp_path / "labs_seed.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    db = session_local()
    try:
        seed_initial_labs(db=db)

        seeded = list(db.scalars(select(Exercise).order_by(Exercise.lab_id.asc(), Exercise.order_index.asc(), Exercise.id.asc())))
        expected_ids = {item["id"] for item in INITIAL_INTERACTIVE_EXERCISES}
        expected_labs = {str(item["id"]) for item in INITIAL_LABS}

        assert len(seeded) == len(INITIAL_INTERACTIVE_EXERCISES)
        assert {item.id for item in seeded} == expected_ids
        assert {item.lab_id for item in seeded} == expected_labs
        assert all(item.status == "published" for item in seeded)
        assert all(item.content_version == 1 for item in seeded)
    finally:
        db.close()
        engine.dispose()


def test_seed_initial_labs_is_idempotent_for_interactive_exercises(tmp_path):
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


def test_seeded_every_lab_has_at_least_one_published_exercise(tmp_path):
    db_file = tmp_path / "labs_seed_coverage.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    db = session_local()
    try:
        seed_initial_labs(db=db)
        seeded = list(db.scalars(select(Exercise).where(Exercise.status == "published")))

        counts_by_lab: dict[str, int] = {}
        for exercise in seeded:
            counts_by_lab[exercise.lab_id] = counts_by_lab.get(exercise.lab_id, 0) + 1

        for lab in INITIAL_LABS:
            assert counts_by_lab.get(str(lab["id"]), 0) >= 1
    finally:
        db.close()
        engine.dispose()


def test_seeded_button_debounce_single_exercise_flags_are_correct(tmp_path):
    db_file = tmp_path / "labs_seed_button_debounce_flags.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    db = session_local()
    try:
        seed_initial_labs(db=db)
        exercises = list(
            db.scalars(
                select(Exercise)
                .where(Exercise.lab_id == "button-debounce-fundamentals")
                .order_by(Exercise.order_index.asc(), Exercise.id.asc())
            )
        )

        assert len(exercises) == 1
        assert exercises[0].is_required is True
        assert exercises[0].status == "published"
        assert exercises[0].max_score == 10
    finally:
        db.close()
        engine.dispose()
