from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.modules.labs.services.lab_service import seed_initial_labs
from app.modules.paths.services.path_service import assign_labs_to_paths, seed_initial_paths
from app.shared.db.base import Base
from app.shared.db.dependencies import get_db


@pytest.fixture
def client(tmp_path) -> TestClient:
    db_file = tmp_path / "path_progress_api.db"
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
        "email": f"path-progress-{uuid4().hex}@example.com",
        "password": "StrongPassword123!",
    }
    register_response = client.post("/api/v1/auth/register", json=payload)
    login_response = client.post("/api/v1/auth/login", json=payload)

    assert register_response.status_code == 201
    assert login_response.status_code == 200

    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def _summary_by_path_name(body: list[dict[str, object]], path_name: str) -> dict[str, object]:
    return next(item for item in body if item["path_name"] == path_name)


def test_me_path_progress_requires_authentication(client: TestClient):
    response = client.get("/api/v1/me/path-progress")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_me_path_progress_no_progress_yet(client: TestClient):
    headers = _auth_headers(client)

    response = client.get("/api/v1/me/path-progress", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 4

    fundamentals = _summary_by_path_name(body, "Embedded Fundamentals")

    assert fundamentals["total_labs"] == 30
    assert fundamentals["completed_labs"] == 0
    assert fundamentals["in_progress_labs"] == 0
    assert fundamentals["locked_labs"] == 29
    assert fundamentals["completion_percentage"] == 0


def test_me_path_progress_one_in_progress(client: TestClient):
    headers = _auth_headers(client)

    start_response = client.post("/api/v1/labs/digital-logic-voltage-levels/start", headers=headers)
    response = client.get("/api/v1/me/path-progress", headers=headers)

    assert start_response.status_code == 200
    assert response.status_code == 200

    fundamentals = _summary_by_path_name(response.json(), "Embedded Fundamentals")
    assert fundamentals["completed_labs"] == 0
    assert fundamentals["in_progress_labs"] == 1
    assert fundamentals["locked_labs"] == 29
    assert fundamentals["completion_percentage"] == 0


def test_me_path_progress_completed_prerequisite_unlocks_next(client: TestClient):
    headers = _auth_headers(client)

    complete_response = client.post("/api/v1/labs/digital-logic-voltage-levels/complete", headers=headers)
    response = client.get("/api/v1/me/path-progress", headers=headers)

    assert complete_response.status_code == 200
    assert response.status_code == 200

    fundamentals = _summary_by_path_name(response.json(), "Embedded Fundamentals")
    assert fundamentals["completed_labs"] == 1
    assert fundamentals["in_progress_labs"] == 0
    assert fundamentals["locked_labs"] == 28
    assert fundamentals["completion_percentage"] == 3


def test_me_path_progress_reopen_prerequisite_updates_percentage_and_locks(client: TestClient):
    headers = _auth_headers(client)

    complete_prereq_response = client.post("/api/v1/labs/digital-logic-voltage-levels/complete", headers=headers)
    complete_next_response = client.post("/api/v1/labs/gpio-led-basics/complete", headers=headers)
    reopen_prereq_response = client.post("/api/v1/labs/digital-logic-voltage-levels/reopen", headers=headers)
    response = client.get("/api/v1/me/path-progress", headers=headers)

    assert complete_prereq_response.status_code == 200
    assert complete_next_response.status_code == 200
    assert reopen_prereq_response.status_code == 200
    assert response.status_code == 200

    fundamentals = _summary_by_path_name(response.json(), "Embedded Fundamentals")
    assert fundamentals["completed_labs"] == 1
    assert fundamentals["in_progress_labs"] == 1
    assert fundamentals["locked_labs"] == 29
    assert fundamentals["completion_percentage"] == 3


def test_me_path_progress_ignores_stale_in_progress_for_locked_lab(client: TestClient):
    headers = _auth_headers(client)

    complete_prereq_response = client.post("/api/v1/labs/digital-logic-voltage-levels/complete", headers=headers)
    start_downstream_response = client.post("/api/v1/labs/gpio-led-basics/start", headers=headers)
    reopen_prereq_response = client.post("/api/v1/labs/digital-logic-voltage-levels/reopen", headers=headers)
    response = client.get("/api/v1/me/path-progress", headers=headers)

    assert complete_prereq_response.status_code == 200
    assert start_downstream_response.status_code == 200
    assert reopen_prereq_response.status_code == 200
    assert response.status_code == 200

    fundamentals = _summary_by_path_name(response.json(), "Embedded Fundamentals")
    assert fundamentals["completed_labs"] == 0
    assert fundamentals["in_progress_labs"] == 1
    assert fundamentals["locked_labs"] == 29
    assert fundamentals["completion_percentage"] == 0
