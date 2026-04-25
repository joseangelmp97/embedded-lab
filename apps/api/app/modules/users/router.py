from fastapi import APIRouter, Depends

from app.modules.auth.dependencies import get_current_user
from app.modules.users.models.user import User
from app.modules.users.schemas.user import UserResponse


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
