from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.auth.dependencies import get_current_user
from app.modules.lab_progress.schemas.lab_progress import LabProgressResponse, PathProgressSummaryResponse
from app.modules.lab_progress.services.lab_progress_service import (
    complete_lab_progress,
    list_user_path_progress_summaries,
    list_user_lab_progress,
    reopen_lab_progress,
    start_lab_progress,
)
from app.modules.users.models.user import User
from app.shared.db.dependencies import get_db


router = APIRouter(tags=["lab_progress"])


@router.get("/me/lab-progress", response_model=list[LabProgressResponse])
def get_my_lab_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[LabProgressResponse]:
    progress_rows = list_user_lab_progress(db=db, user_id=current_user.id)
    return [LabProgressResponse.model_validate(progress_row) for progress_row in progress_rows]


@router.get("/me/path-progress", response_model=list[PathProgressSummaryResponse])
def get_my_path_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PathProgressSummaryResponse]:
    summaries = list_user_path_progress_summaries(db=db, user_id=current_user.id)
    return [PathProgressSummaryResponse.model_validate(summary) for summary in summaries]


@router.post("/labs/{lab_id}/start", response_model=LabProgressResponse)
def start_lab(
    lab_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LabProgressResponse:
    progress = start_lab_progress(db=db, user=current_user, lab_id=lab_id)
    return LabProgressResponse.model_validate(progress)


@router.post("/labs/{lab_id}/complete", response_model=LabProgressResponse)
def complete_lab(
    lab_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LabProgressResponse:
    progress = complete_lab_progress(db=db, user=current_user, lab_id=lab_id)
    return LabProgressResponse.model_validate(progress)


@router.post("/labs/{lab_id}/reopen", response_model=LabProgressResponse)
def reopen_lab(
    lab_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LabProgressResponse:
    progress = reopen_lab_progress(db=db, user=current_user, lab_id=lab_id)
    return LabProgressResponse.model_validate(progress)
