from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.users.models.user import User
from app.shared.config.settings import get_settings
from app.shared.db.dependencies import get_db


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    unauthorized_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    settings = get_settings()

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.auth_jwt_secret_key,
            algorithms=[settings.auth_jwt_algorithm],
        )
    except JWTError as exc:
        raise unauthorized_exception from exc

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise unauthorized_exception

    user = db.scalar(select(User).where(User.id == subject))
    if user is None:
        raise unauthorized_exception

    return user
