from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.auth.dependencies import get_current_user
from app.modules.labs.schemas.lab import LabResponse
from app.modules.paths.services.path_module_service import list_labs_by_module_id
from app.modules.users.models.user import User
from app.shared.db.dependencies import get_db


router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("/{module_id}/labs", response_model=list[LabResponse])
def get_module_labs(
    module_id: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[LabResponse]:
    labs = list_labs_by_module_id(db=db, module_id=module_id)
    return [LabResponse.model_validate(lab) for lab in labs]
