from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.shared.db.base import Base
from app.shared.db.dependencies import get_db


@pytest.fixture
def client(tmp_path) -> TestClient:
    db_file = tmp_path / "auth_register.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    engine.dispose()


def test_register_returns_201_for_valid_payload(client: TestClient):
    payload = {
        "email": f"learner-{uuid4().hex}@example.com",
        "password": "StrongPassword123!",
    }

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == payload["email"]
    assert body["role"] == "learner"
    assert body["status"] == "active"
    assert "id" in body
    assert "created_at" in body


def test_register_returns_409_when_email_already_exists(client: TestClient):
    email = f"duplicate-{uuid4().hex}@example.com"
    payload = {
        "email": email,
        "password": "StrongPassword123!",
    }

    first_response = client.post("/api/v1/auth/register", json=payload)
    second_response = client.post("/api/v1/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Email already exists"


def test_register_rejects_password_longer_than_72_bytes(client: TestClient):
    payload = {
        "email": f"limit-{uuid4().hex}@example.com",
        "password": "a" * 73,
    }

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(item["loc"] == ["body", "password"] for item in detail)


def test_login_returns_token_for_valid_credentials(client: TestClient):
    payload = {
        "email": f"login-{uuid4().hex}@example.com",
        "password": "StrongPassword123!",
    }

    register_response = client.post("/api/v1/auth/register", json=payload)
    login_response = client.post("/api/v1/auth/login", json=payload)

    assert register_response.status_code == 201
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


def test_login_returns_401_for_invalid_credentials(client: TestClient):
    payload = {
        "email": f"wrong-pass-{uuid4().hex}@example.com",
        "password": "StrongPassword123!",
    }

    register_response = client.post("/api/v1/auth/register", json=payload)
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": "WrongPassword123!"},
    )

    assert register_response.status_code == 201
    assert login_response.status_code == 401
    assert login_response.json()["detail"] == "Invalid credentials"
