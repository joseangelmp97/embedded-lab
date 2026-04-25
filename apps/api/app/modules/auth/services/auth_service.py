from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.security import create_access_token, hash_password, verify_password
from app.modules.users.models.user import User
from app.modules.users.schemas.user import UserCreate, UserLogin


def register_user(db: Session, payload: UserCreate) -> User:
    existing_user = db.scalar(select(User).where(User.email == str(payload.email)))

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    user = User(
        email=str(payload.email),
        password_hash=hash_password(payload.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def login_user(db: Session, payload: UserLogin) -> str:
    user = db.scalar(select(User).where(User.email == str(payload.email)))

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return create_access_token(subject=user.id)
