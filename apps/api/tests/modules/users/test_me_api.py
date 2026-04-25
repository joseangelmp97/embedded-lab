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
    db_file = tmp_path / "users_me.db"
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


def test_me_returns_authenticated_user(client: TestClient):
    payload = {
        "email": f"me-{uuid4().hex}@example.com",
        "password": "StrongPassword123!",
    }

    register_response = client.post("/api/v1/auth/register", json=payload)
    login_response = client.post("/api/v1/auth/login", json=payload)
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert register_response.status_code == 201
    assert login_response.status_code == 200
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == payload["email"]
    assert body["role"] == "learner"
    assert body["status"] == "active"


def test_me_returns_401_without_token(client: TestClient):
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_me_returns_401_for_invalid_token(client: TestClient):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_openapi_uses_http_bearer_for_me_endpoint(client: TestClient):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    openapi = response.json()
    security_schemes = openapi["components"]["securitySchemes"]
    scheme_name = next(iter(security_schemes))
    scheme = security_schemes[scheme_name]

    assert scheme["type"] == "http"
    assert scheme["scheme"] == "bearer"
    assert {scheme_name: []} in openapi["paths"]["/api/v1/users/me"]["get"]["security"]
