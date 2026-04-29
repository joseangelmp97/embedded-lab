from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.auth.dependencies import get_current_user
from app.modules.labs.schemas.lab import LabResponse
from app.modules.paths.schemas.path_module import PathModuleResponse
from app.modules.paths.schemas.path import PathResponse
from app.modules.paths.services.path_service import list_labs_by_path_id, list_paths
from app.modules.paths.services.path_module_service import list_modules_by_path_id
from app.modules.users.models.user import User
from app.shared.db.dependencies import get_db


router = APIRouter(prefix="/paths", tags=["paths"])


@router.get("", response_model=list[PathResponse])
def get_paths(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PathResponse]:
    paths = list_paths(db=db)
    return [PathResponse.model_validate(path) for path in paths]


@router.get("/{path_id}/labs", response_model=list[LabResponse])
def get_path_labs(
    path_id: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[LabResponse]:
    labs = list_labs_by_path_id(db=db, path_id=path_id)
    return [LabResponse.model_validate(lab) for lab in labs]


@router.get("/{path_id}/modules", response_model=list[PathModuleResponse])
def get_path_modules(
    path_id: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PathModuleResponse]:
    modules = list_modules_by_path_id(db=db, path_id=path_id)
    return [PathModuleResponse.model_validate(module) for module in modules]

