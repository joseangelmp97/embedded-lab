from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.modules.attempts.models.lab_attempt_session import LabAttemptSession
from app.modules.labs.services.lab_service import INITIAL_LABS, seed_initial_labs
from app.modules.paths.services.path_service import assign_labs_to_paths, seed_initial_paths
from app.shared.db.base import Base
from app.shared.db.dependencies import get_db


@pytest.fixture
def test_context(tmp_path):
    db_file = tmp_path / "attempts_api.db"
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
        yield {"client": test_client, "session_local": testing_session_local}

    app.dependency_overrides.clear()
    engine.dispose()


def _auth_headers(client: TestClient) -> dict[str, str]:
    payload = {
        "email": f"attempts-{uuid4().hex}@example.com",
        "password": "StrongPassword123!",
    }
    register_response = client.post("/api/v1/auth/register", json=payload)
    login_response = client.post("/api/v1/auth/login", json=payload)

    assert register_response.status_code == 201
    assert login_response.status_code == 200

    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def test_create_first_attempt(test_context):
    client = test_context["client"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])

    response = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["lab_id"] == lab_id
    assert body["attempt_number"] == 1
    assert body["lab_attempt_status"] == "started"


def test_repeated_post_resumes_active_attempt(test_context):
    client = test_context["client"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])

    first_response = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers)
    second_response = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["id"] == second_response.json()["id"]
    assert second_response.json()["attempt_number"] == 1


def test_closed_prior_attempt_creates_next_attempt_number(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])

    first_response = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers)
    assert first_response.status_code == 200

    db = session_local()
    try:
        attempt = db.scalar(select(LabAttemptSession).where(LabAttemptSession.id == first_response.json()["id"]))
        assert attempt is not None
        attempt.lab_attempt_status = "completed"
        db.commit()
    finally:
        db.close()

    second_response = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers)
    assert second_response.status_code == 200
    assert second_response.json()["attempt_number"] == 2
    assert second_response.json()["id"] != first_response.json()["id"]


def test_get_own_attempt_succeeds(test_context):
    client = test_context["client"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])

    create_response = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers)
    attempt_id = create_response.json()["id"]

    response = client.get(f"/api/v1/labs/{lab_id}/attempts/{attempt_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == attempt_id


def test_get_other_user_attempt_returns_404(test_context):
    client = test_context["client"]
    owner_headers = _auth_headers(client)
    other_headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])

    create_response = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=owner_headers)
    attempt_id = create_response.json()["id"]

    response = client.get(f"/api/v1/labs/{lab_id}/attempts/{attempt_id}", headers=other_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Attempt not found"


def test_attempt_endpoints_require_authentication(test_context):
    client = test_context["client"]
    lab_id = str(INITIAL_LABS[0]["id"])

    post_response = client.post(f"/api/v1/labs/{lab_id}/attempts")
    get_response = client.get(f"/api/v1/labs/{lab_id}/attempts/some-attempt")

    assert post_response.status_code == 401
    assert get_response.status_code == 401


def test_missing_lab_returns_404(test_context):
    client = test_context["client"]
    headers = _auth_headers(client)

    response = client.post("/api/v1/labs/non-existing-lab/attempts", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Lab not found"


def test_locked_lab_cannot_create_attempt(test_context):
    client = test_context["client"]
    headers = _auth_headers(client)
    locked_lab_id = str(INITIAL_LABS[2]["id"])

    response = client.post(f"/api/v1/labs/{locked_lab_id}/attempts", headers=headers)

    assert response.status_code == 403
    assert "Lab is locked" in response.json()["detail"]


def test_lab_progress_endpoints_behavior_remains_unchanged(test_context):
    client = test_context["client"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])

    create_attempt_response = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers)
    start_response = client.post(f"/api/v1/labs/{lab_id}/start", headers=headers)
    complete_response = client.post(f"/api/v1/labs/{lab_id}/complete", headers=headers)
    reopen_response = client.post(f"/api/v1/labs/{lab_id}/reopen", headers=headers)

    assert create_attempt_response.status_code == 200
    assert start_response.status_code == 200
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"
    assert reopen_response.status_code == 200
    assert reopen_response.json()["status"] == "in_progress"
