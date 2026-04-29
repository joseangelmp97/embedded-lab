from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.attempts.models.lab_attempt_session import LabAttemptSession
from app.modules.lab_progress.services.lab_progress_service import start_lab_progress
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
