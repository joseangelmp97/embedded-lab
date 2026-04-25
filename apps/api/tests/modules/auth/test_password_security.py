import pytest
from pydantic import ValidationError

from app.modules.auth.security import hash_password, verify_password
from app.modules.users.schemas.user import UserCreate


def test_hash_and_verify_password_round_trip():
    password = "StrongPassword123!"

    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$2")
    assert verify_password(password, password_hash)


def test_user_create_rejects_password_over_72_utf8_bytes():
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            email="bytes-limit@example.com",
            password="á" * 37,
        )

    assert "at most 72 bytes" in str(exc_info.value)
