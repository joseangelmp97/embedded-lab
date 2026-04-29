from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.auth.dependencies import get_current_user
from app.modules.labs.schemas.exercise import ExerciseListItemResponse
from app.modules.labs.schemas.lab import LabResponse
from app.modules.labs.services.lab_service import (
    get_lab_by_id,
    list_labs,
    list_published_lab_exercises,
    parse_and_sanitize_json,
)
from app.modules.users.models.user import User
from app.shared.db.dependencies import get_db


router = APIRouter(prefix="/labs", tags=["labs"])


@router.get("", response_model=list[LabResponse])
def get_labs(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[LabResponse]:
    labs = list_labs(db=db)
    return [LabResponse.model_validate(lab) for lab in labs]


@router.get("/{lab_id}", response_model=LabResponse)
def get_lab(
    lab_id: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LabResponse:
    lab = get_lab_by_id(db=db, lab_id=lab_id)
    return LabResponse.model_validate(lab)


@router.get("/{lab_id}/exercises", response_model=list[ExerciseListItemResponse])
def get_lab_exercises(
    lab_id: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ExerciseListItemResponse]:
    exercises = list_published_lab_exercises(db=db, lab_id=lab_id)
    return [
        ExerciseListItemResponse(
            id=exercise.id,
            exercise_type=exercise.exercise_type,
            prompt=exercise.prompt,
            order_index=exercise.order_index,
            max_score=exercise.max_score,
            metadata_json=parse_and_sanitize_json(exercise.metadata_json),
            hint_policy_json=parse_and_sanitize_json(exercise.hint_policy_json),
            explanation=exercise.explanation,
        )
        for exercise in exercises
    ]
