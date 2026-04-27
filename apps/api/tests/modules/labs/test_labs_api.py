from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.modules.labs.services.lab_service import INITIAL_LABS, seed_initial_labs
from app.shared.db.base import Base
from app.shared.db.dependencies import get_db


@pytest.fixture
def client(tmp_path) -> TestClient:
    db_file = tmp_path / "labs_api.db"
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

    seed_db = testing_session_local()
    try:
        seed_initial_labs(db=seed_db)
    finally:
        seed_db.close()

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


def _authenticate(client: TestClient) -> str:
    payload = {
        "email": f"labs-{uuid4().hex}@example.com",
        "password": "StrongPassword123!",
    }
    register_response = client.post("/api/v1/auth/register", json=payload)
    login_response = client.post("/api/v1/auth/login", json=payload)

    assert register_response.status_code == 201
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def test_labs_list_returns_seeded_labs_for_authenticated_user(client: TestClient):
    token = _authenticate(client)

    response = client.get("/api/v1/labs", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == len(INITIAL_LABS)
    assert [lab["id"] for lab in body] == [lab["id"] for lab in INITIAL_LABS]


def test_lab_detail_returns_requested_lab(client: TestClient):
    token = _authenticate(client)
    lab_id = INITIAL_LABS[0]["id"]

    response = client.get(f"/api/v1/labs/{lab_id}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == lab_id
    assert body["title"] == INITIAL_LABS[0]["title"]


def test_labs_list_requires_authentication(client: TestClient):
    response = client.get("/api/v1/labs")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
