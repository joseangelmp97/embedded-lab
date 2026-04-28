from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.modules.labs.services.lab_service import INITIAL_LABS, seed_initial_labs
from app.modules.paths.services.path_service import assign_labs_to_paths, seed_initial_paths
from app.shared.db.base import Base
from app.shared.db.dependencies import get_db


@pytest.fixture
def client(tmp_path) -> TestClient:
    db_file = tmp_path / "lab_progress_api.db"
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
        seed_initial_paths(db=seed_db)
        seed_initial_labs(db=seed_db)
        assign_labs_to_paths(db=seed_db)
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


def _auth_headers(client: TestClient) -> dict[str, str]:
    payload = {
        "email": f"progress-{uuid4().hex}@example.com",
        "password": "StrongPassword123!",
    }
    register_response = client.post("/api/v1/auth/register", json=payload)
    login_response = client.post("/api/v1/auth/login", json=payload)

    assert register_response.status_code == 201
    assert login_response.status_code == 200

    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def test_my_lab_progress_returns_empty_list_for_new_user(client: TestClient):
    headers = _auth_headers(client)

    response = client.get("/api/v1/me/lab-progress", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


def test_start_unlocked_lab_is_idempotent(client: TestClient):
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])

    first_response = client.post(f"/api/v1/labs/{lab_id}/start", headers=headers)
    second_response = client.post(f"/api/v1/labs/{lab_id}/start", headers=headers)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["id"] == second_response.json()["id"]
    assert second_response.json()["status"] == "in_progress"
    assert second_response.json()["completed_at"] is None


def test_start_locked_lab_returns_403(client: TestClient):
    headers = _auth_headers(client)
    locked_lab_id = str(INITIAL_LABS[2]["id"])

    response = client.post(f"/api/v1/labs/{locked_lab_id}/start", headers=headers)

    assert response.status_code == 403
    assert "Lab is locked" in response.json()["detail"]


def test_complete_prerequisite_unlocks_next_lab(client: TestClient):
    headers = _auth_headers(client)
    prerequisite_lab_id = str(INITIAL_LABS[1]["id"])
    next_lab_id = str(INITIAL_LABS[2]["id"])

    locked_response = client.post(f"/api/v1/labs/{next_lab_id}/start", headers=headers)
    complete_prerequisite_response = client.post(f"/api/v1/labs/{prerequisite_lab_id}/complete", headers=headers)
    unlocked_response = client.post(f"/api/v1/labs/{next_lab_id}/start", headers=headers)

    assert locked_response.status_code == 403
    assert complete_prerequisite_response.status_code == 200
    assert unlocked_response.status_code == 200
    assert unlocked_response.json()["status"] == "in_progress"


def test_complete_lab_creates_progress_if_missing(client: TestClient):
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[1]["id"])

    response = client.post(f"/api/v1/labs/{lab_id}/complete", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["started_at"] is not None
    assert body["completed_at"] is not None


def test_reopen_completed_lab_sets_in_progress_and_clears_completed_at(client: TestClient):
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[2]["id"])

    complete_response = client.post(f"/api/v1/labs/{lab_id}/complete", headers=headers)
    reopen_response = client.post(f"/api/v1/labs/{lab_id}/reopen", headers=headers)

    assert complete_response.status_code == 200
    assert reopen_response.status_code == 200
    body = reopen_response.json()
    assert body["status"] == "in_progress"
    assert body["started_at"] is not None
    assert body["completed_at"] is None


def test_progress_actions_return_404_for_missing_lab(client: TestClient):
    headers = _auth_headers(client)

    response = client.post("/api/v1/labs/non-existing-lab/start", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Lab not found"


def test_lab_progress_endpoints_require_authentication(client: TestClient):
    response = client.get("/api/v1/me/lab-progress")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
