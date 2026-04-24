from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.shared.config.settings import get_settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expires_delta = timedelta(minutes=settings.auth_access_token_expire_minutes)
    expire = datetime.now(UTC) + expires_delta

    payload = {
        "sub": subject,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.auth_jwt_secret_key,
        algorithm=settings.auth_jwt_algorithm,
    )
