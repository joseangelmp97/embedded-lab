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


def _complete_lab_via_evaluation(client: TestClient, headers: dict[str, str], lab_id: str) -> None:
    attempt_id = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers).json()["id"]

    if lab_id == "digital-logic-voltage-levels":
        first_submit = client.post(
            f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
            headers=headers,
            json={"exercise_id": "ex-digital-logic-mcq-thresholds", "response_payload_json": {"selected_option_id": "opt-high"}},
        )
        second_submit = client.post(
            f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
            headers=headers,
            json={"exercise_id": "ex-digital-logic-fill-signal-chain", "response_payload_json": {"answers": ["output", "high"]}},
        )
    elif lab_id == "gpio-led-basics":
        first_submit = client.post(
            f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
            headers=headers,
            json={"exercise_id": "ex-gpio-led-fill-polarity", "response_payload_json": {"answers": ["anode", "cathode"]}},
        )
        second_submit = client.post(
            f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
            headers=headers,
            json={
                "exercise_id": "ex-gpio-led-short-current-limiting",
                "response_payload_json": {"answer": "A resistor helps limit current and protect LED operation."},
            },
        )
    else:
        raise AssertionError(f"Unsupported seeded lab for evaluation helper: {lab_id}")

    assert first_submit.status_code == 200
    assert second_submit.status_code == 200


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


def test_me_path_progress_manual_complete_does_not_unlock_next(client: TestClient):
    headers = _auth_headers(client)

    complete_response = client.post("/api/v1/labs/digital-logic-voltage-levels/complete", headers=headers)
    response = client.get("/api/v1/me/path-progress", headers=headers)

    assert complete_response.status_code == 409
    assert "Manual completion is not allowed for interactive labs" in complete_response.json()["detail"]
    assert response.status_code == 200

    fundamentals = _summary_by_path_name(response.json(), "Embedded Fundamentals")
    assert fundamentals["completed_labs"] == 0
    assert fundamentals["in_progress_labs"] == 0
    assert fundamentals["locked_labs"] == 29
    assert fundamentals["completion_percentage"] == 0


def test_me_path_progress_reopen_prerequisite_updates_percentage_and_locks(client: TestClient):
    headers = _auth_headers(client)

    _complete_lab_via_evaluation(client=client, headers=headers, lab_id="digital-logic-voltage-levels")
    _complete_lab_via_evaluation(client=client, headers=headers, lab_id="gpio-led-basics")
    reopen_prereq_response = client.post("/api/v1/labs/digital-logic-voltage-levels/reopen", headers=headers)
    response = client.get("/api/v1/me/path-progress", headers=headers)

    assert reopen_prereq_response.status_code == 200
    assert response.status_code == 200

    fundamentals = _summary_by_path_name(response.json(), "Embedded Fundamentals")
    assert fundamentals["completed_labs"] == 1
    assert fundamentals["in_progress_labs"] == 1
    assert fundamentals["locked_labs"] == 29
    assert fundamentals["completion_percentage"] == 3


def test_me_path_progress_evaluated_completion_unlocks_next(client: TestClient):
    headers = _auth_headers(client)

    _complete_lab_via_evaluation(client=client, headers=headers, lab_id="digital-logic-voltage-levels")
    response = client.get("/api/v1/me/path-progress", headers=headers)

    assert response.status_code == 200

    fundamentals = _summary_by_path_name(response.json(), "Embedded Fundamentals")
    assert fundamentals["completed_labs"] == 1
    assert fundamentals["in_progress_labs"] == 0
    assert fundamentals["locked_labs"] == 28
    assert fundamentals["completion_percentage"] == 3


def test_me_path_progress_ignores_stale_in_progress_for_locked_lab(client: TestClient):
    headers = _auth_headers(client)

    _complete_lab_via_evaluation(client=client, headers=headers, lab_id="digital-logic-voltage-levels")
    start_downstream_response = client.post("/api/v1/labs/gpio-led-basics/start", headers=headers)
    reopen_prereq_response = client.post("/api/v1/labs/digital-logic-voltage-levels/reopen", headers=headers)
    response = client.get("/api/v1/me/path-progress", headers=headers)

    assert start_downstream_response.status_code == 200
    assert reopen_prereq_response.status_code == 200
    assert response.status_code == 200

    fundamentals = _summary_by_path_name(response.json(), "Embedded Fundamentals")
    assert fundamentals["completed_labs"] == 0
    assert fundamentals["in_progress_labs"] == 1
    assert fundamentals["locked_labs"] == 29
    assert fundamentals["completion_percentage"] == 0
