from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


MAX_BCRYPT_PASSWORD_BYTES = 72


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password_bcrypt_limit(cls, value: str) -> str:
        if len(value.encode("utf-8")) > MAX_BCRYPT_PASSWORD_BYTES:
            raise ValueError(
                "Password must be at most 72 bytes for bcrypt compatibility",
            )

        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
