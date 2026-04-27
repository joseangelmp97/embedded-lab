from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.auth.dependencies import get_current_user
from app.modules.labs.schemas.lab import LabResponse
from app.modules.labs.services.lab_service import get_lab_by_id, list_labs
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
