import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.attempts.models.exercise_attempt import ExerciseAttempt
from app.modules.attempts.models.lab_attempt_session import LabAttemptSession
from app.modules.evaluation.services import evaluate_exercise_submission
from app.modules.lab_progress.services.lab_progress_service import start_lab_progress
from app.modules.labs.models.exercise import Exercise
from app.modules.labs.services.lab_service import get_lab_by_id, list_published_lab_exercises
from app.modules.users.models.user import User


ACTIVE_LAB_ATTEMPT_STATUSES = {"started"}


def create_or_resume_lab_attempt(db: Session, user: User, lab_id: str) -> LabAttemptSession:
    start_lab_progress(db=db, user=user, lab_id=lab_id)
    lab = get_lab_by_id(db=db, lab_id=lab_id)

    active_attempt = db.scalar(
        select(LabAttemptSession)
        .where(
            LabAttemptSession.user_id == user.id,
            LabAttemptSession.lab_id == lab_id,
            LabAttemptSession.lab_attempt_status.in_(ACTIVE_LAB_ATTEMPT_STATUSES),
        )
        .order_by(LabAttemptSession.attempt_number.desc()),
    )
    if active_attempt is not None:
        return active_attempt

    latest_attempt_number = db.scalar(
        select(func.max(LabAttemptSession.attempt_number)).where(
            LabAttemptSession.user_id == user.id,
            LabAttemptSession.lab_id == lab_id,
        ),
    )
    next_attempt_number = int(latest_attempt_number or 0) + 1

    exercises = list_published_lab_exercises(db=db, lab_id=lab_id)
    max_score = sum(exercise.max_score for exercise in exercises)
    required_total = sum(1 for exercise in exercises if exercise.is_required)

    attempt = LabAttemptSession(
        user_id=user.id,
        lab_id=lab_id,
        attempt_number=next_attempt_number,
        lab_attempt_status="started",
        total_score_awarded=0,
        max_score=max_score,
        required_exercises_correct=0,
        required_exercises_total=required_total,
        hints_used_count=0,
        content_version=lab.content_version,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def get_user_lab_attempt(db: Session, user_id: str, lab_id: str, attempt_id: str) -> LabAttemptSession:
    get_lab_by_id(db=db, lab_id=lab_id)

    attempt = db.scalar(
        select(LabAttemptSession).where(
            LabAttemptSession.id == attempt_id,
            LabAttemptSession.lab_id == lab_id,
            LabAttemptSession.user_id == user_id,
        ),
    )
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")

    return attempt


def _recompute_attempt_aggregates(db: Session, attempt: LabAttemptSession) -> None:
    exercise_scores = db.execute(
        select(ExerciseAttempt.exercise_id, func.max(ExerciseAttempt.score_awarded))
        .where(ExerciseAttempt.lab_attempt_session_id == attempt.id)
        .group_by(ExerciseAttempt.exercise_id)
    ).all()
    attempt.total_score_awarded = sum(int(row[1] or 0) for row in exercise_scores)

    required_best_scores = db.execute(
        select(Exercise.id, func.max(ExerciseAttempt.score_awarded))
        .join(ExerciseAttempt, ExerciseAttempt.exercise_id == Exercise.id)
        .where(
            ExerciseAttempt.lab_attempt_session_id == attempt.id,
            Exercise.is_required.is_(True),
        )
        .group_by(Exercise.id)
    ).all()
    attempt.required_exercises_correct = sum(1 for _, best_score in required_best_scores if int(best_score or 0) > 0)


def submit_lab_exercise_attempt(
    db: Session,
    user_id: str,
    lab_id: str,
    attempt_id: str,
    exercise_id: str,
    response_payload_json: dict,
) -> tuple[ExerciseAttempt, LabAttemptSession]:
    get_lab_by_id(db=db, lab_id=lab_id)

    attempt = db.scalar(select(LabAttemptSession).where(LabAttemptSession.id == attempt_id))
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    if attempt.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Attempt does not belong to current user")
    if attempt.lab_id != lab_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found for lab")
    if attempt.lab_attempt_status != "started":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Attempt is not active")

    exercise = db.scalar(select(Exercise).where(Exercise.id == exercise_id))
    if exercise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
    if exercise.lab_id != lab_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found for lab")
    evaluation = evaluate_exercise_submission(
        exercise_type=exercise.exercise_type,
        metadata_json=exercise.metadata_json,
        response_payload_json=response_payload_json,
        max_score=exercise.max_score,
    )

    latest_sequence = db.scalar(
        select(func.max(ExerciseAttempt.attempt_sequence)).where(ExerciseAttempt.lab_attempt_session_id == attempt.id)
    )
    next_sequence = int(latest_sequence or 0) + 1

    exercise_attempt = ExerciseAttempt(
        lab_attempt_session_id=attempt.id,
        exercise_id=exercise.id,
        response_payload_json=json.dumps(response_payload_json),
        is_correct=evaluation.is_correct,
        score_awarded=evaluation.score_awarded,
        max_score=exercise.max_score,
        feedback=evaluation.feedback,
        evaluation_details_json=json.dumps(evaluation.details),
        attempt_sequence=next_sequence,
        evaluated_at=datetime.now(timezone.utc),
    )
    db.add(exercise_attempt)
    db.flush()

    _recompute_attempt_aggregates(db=db, attempt=attempt)
    db.commit()
    db.refresh(exercise_attempt)
    db.refresh(attempt)
    return exercise_attempt, attempt
