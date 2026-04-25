from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.modules.auth.schemas.token import TokenResponse
from app.modules.auth.services.auth_service import login_user, register_user
from app.modules.users.schemas.user import UserCreate, UserLogin, UserResponse
from app.shared.db.dependencies import get_db


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    user = register_user(db=db, payload=payload)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    access_token = login_user(db=db, payload=payload)
    return TokenResponse(access_token=access_token)
