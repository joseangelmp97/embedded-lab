from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.attempts.schemas.lab_attempt import (
    AttemptSessionSummaryResponse,
    ExerciseSubmitRequest,
    ExerciseSubmitResponse,
    LabAttemptSessionResponse,
)
from app.modules.attempts.services.attempt_service import (
    create_or_resume_lab_attempt,
    get_user_lab_attempt,
    submit_lab_exercise_attempt,
)
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models.user import User
from app.shared.db.dependencies import get_db


router = APIRouter(tags=["attempts"])


@router.post("/labs/{lab_id}/attempts", response_model=LabAttemptSessionResponse)
def create_lab_attempt(
    lab_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LabAttemptSessionResponse:
    attempt = create_or_resume_lab_attempt(db=db, user=current_user, lab_id=lab_id)
    return LabAttemptSessionResponse.model_validate(attempt)


@router.get("/labs/{lab_id}/attempts/{attempt_id}", response_model=LabAttemptSessionResponse)
def get_lab_attempt(
    lab_id: str,
    attempt_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LabAttemptSessionResponse:
    attempt = get_user_lab_attempt(db=db, user_id=current_user.id, lab_id=lab_id, attempt_id=attempt_id)
    return LabAttemptSessionResponse.model_validate(attempt)


@router.post("/labs/{lab_id}/attempts/{attempt_id}/submit", response_model=ExerciseSubmitResponse)
def submit_lab_attempt(
    lab_id: str,
    attempt_id: str,
    payload: ExerciseSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExerciseSubmitResponse:
    exercise_attempt, attempt = submit_lab_exercise_attempt(
        db=db,
        user_id=current_user.id,
        lab_id=lab_id,
        attempt_id=attempt_id,
        exercise_id=payload.exercise_id,
        response_payload_json=payload.response_payload_json,
    )
    return ExerciseSubmitResponse(
        exercise_attempt_id=exercise_attempt.id,
        is_correct=bool(exercise_attempt.is_correct),
        score_awarded=exercise_attempt.score_awarded,
        max_score=exercise_attempt.max_score,
        feedback=exercise_attempt.feedback or "",
        session=AttemptSessionSummaryResponse.model_validate(attempt),
    )
