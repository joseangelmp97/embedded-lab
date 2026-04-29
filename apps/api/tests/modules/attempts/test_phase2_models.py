from sqlalchemy import create_engine, event, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.modules.attempts.models.exercise_attempt import ExerciseAttempt
from app.modules.attempts.models.lab_attempt_session import LabAttemptSession
from app.modules.labs.models.exercise import Exercise
from app.modules.labs.models.lab import Lab
from app.modules.paths.models.path import Path
from app.modules.paths.models.path_module import PathModule
from app.modules.users.models.user import User
from app.shared.db.base import Base


def _sqlite_session_factory(db_file):
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    testing_session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    return engine, testing_session_local


def test_phase2_tables_are_created_in_metadata_create_all(tmp_path):
    db_file = tmp_path / "phase2_model_tables.db"
    engine, _ = _sqlite_session_factory(db_file)
    try:
        Base.metadata.create_all(bind=engine)
        table_names = set(inspect(engine).get_table_names())

        assert "exercises" in table_names
        assert "lab_attempt_sessions" in table_names
        assert "exercise_attempts" in table_names
    finally:
        engine.dispose()


def test_phase2_models_enforce_sqlite_foreign_keys(tmp_path):
    db_file = tmp_path / "phase2_model_fks.db"
    engine, testing_session_local = _sqlite_session_factory(db_file)

    try:
        Base.metadata.create_all(bind=engine)

        db = testing_session_local()
        try:
            user = User(email="phase2@example.com", password_hash="hash")
            lab = Lab(
                id="phase2-lab",
                title="Phase 2 lab",
                description="Model skeleton validation lab",
                difficulty="beginner",
                estimated_minutes=10,
                status="published",
                order_index=1,
            )
            db.add(user)
            db.add(lab)
            db.commit()

            session_row = LabAttemptSession(
                user_id=user.id,
                lab_id=lab.id,
                attempt_number=1,
                lab_attempt_status="started",
                total_score_awarded=0,
                max_score=100,
                required_exercises_correct=0,
                required_exercises_total=1,
                hints_used_count=0,
                content_version=1,
            )
            db.add(session_row)
            db.commit()

            exercise = Exercise(
                lab_id=lab.id,
                exercise_type="multiple_choice",
                prompt="Select the safe GPIO current range.",
                order_index=1,
                max_score=100,
                is_required=True,
                status="published",
                content_version=1,
            )
            db.add(exercise)
            db.commit()

            valid_attempt = ExerciseAttempt(
                lab_attempt_session_id=session_row.id,
                exercise_id=exercise.id,
                response_payload_json='{"answer":"A"}',
                is_correct=True,
                score_awarded=100,
                max_score=100,
                attempt_sequence=1,
            )
            db.add(valid_attempt)
            db.commit()

            invalid_attempt = ExerciseAttempt(
                lab_attempt_session_id="missing-session",
                exercise_id=exercise.id,
                response_payload_json='{"answer":"B"}',
                is_correct=False,
                score_awarded=0,
                max_score=100,
                attempt_sequence=2,
            )
            db.add(invalid_attempt)

            try:
                db.commit()
                assert False, "Expected FK violation for missing lab_attempt_session"
            except IntegrityError:
                db.rollback()
        finally:
            db.close()
    finally:
        engine.dispose()
