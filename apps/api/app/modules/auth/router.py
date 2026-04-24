from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.modules.auth.services.auth_service import register_user
from app.modules.users.schemas.user import UserCreate, UserResponse
from app.shared.db.dependencies import get_db


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    user = register_user(db=db, payload=payload)
    return UserResponse.model_validate(user)
