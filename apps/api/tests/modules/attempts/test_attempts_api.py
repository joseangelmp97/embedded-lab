from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.modules.attempts.models.lab_attempt_session import LabAttemptSession
from app.modules.labs.models.exercise import Exercise
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


def _create_exercise(
    session_local,
    lab_id: str,
    exercise_id: str,
    exercise_type: str,
    metadata_json: str,
    max_score: int = 10,
    is_required: bool = True,
):
    db = session_local()
    try:
        db.add(
            Exercise(
                id=exercise_id,
                lab_id=lab_id,
                exercise_type=exercise_type,
                prompt="Pick the correct option",
                order_index=1,
                max_score=max_score,
                is_required=is_required,
                status="published",
                metadata_json=metadata_json,
            )
        )
        db.commit()
    finally:
        db.close()


def _create_mcq_exercise(
    session_local,
    lab_id: str,
    exercise_id: str = "exercise-mcq",
    exercise_type: str = "multiple_choice",
    is_required: bool = True,
):
    _create_exercise(
        session_local=session_local,
        lab_id=lab_id,
        exercise_id=exercise_id,
        exercise_type=exercise_type,
        metadata_json='{"correct_option_id":"opt-a"}',
        is_required=is_required,
    )


def test_submit_correct_mcq_returns_full_score(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_mcq_exercise(session_local=session_local, lab_id=lab_id)

    attempt_response = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers)
    attempt_id = attempt_response.json()["id"]

    response = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-mcq", "response_payload_json": {"selected_option_id": "opt-a"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_correct"] is True
    assert body["score_awarded"] == 10
    assert body["max_score"] == 10
    assert body["session"]["total_score_awarded"] == 10


def test_submit_incorrect_mcq_returns_zero_score(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_mcq_exercise(session_local=session_local, lab_id=lab_id)

    attempt_response = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers)
    attempt_id = attempt_response.json()["id"]

    response = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-mcq", "response_payload_json": {"selected_option_id": "opt-b"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_correct"] is False
    assert body["score_awarded"] == 0
    assert body["session"]["total_score_awarded"] == 0


def test_submit_enforces_attempt_ownership(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    owner_headers = _auth_headers(client)
    other_headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_mcq_exercise(session_local=session_local, lab_id=lab_id)

    attempt_response = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=owner_headers)
    attempt_id = attempt_response.json()["id"]

    response = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=other_headers,
        json={"exercise_id": "exercise-mcq", "response_payload_json": {"selected_option_id": "opt-a"}},
    )

    assert response.status_code == 403


def test_submit_rejects_attempt_and_lab_mismatch(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    source_lab_id = str(INITIAL_LABS[0]["id"])
    other_lab_id = str(INITIAL_LABS[1]["id"])
    _create_mcq_exercise(session_local=session_local, lab_id=source_lab_id)

    attempt_response = client.post(f"/api/v1/labs/{source_lab_id}/attempts", headers=headers)
    attempt_id = attempt_response.json()["id"]

    response = client.post(
        f"/api/v1/labs/{other_lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-mcq", "response_payload_json": {"selected_option_id": "opt-a"}},
    )

    assert response.status_code == 404


def test_submit_rejects_inactive_attempt(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_mcq_exercise(session_local=session_local, lab_id=lab_id)

    attempt_response = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers)
    attempt_id = attempt_response.json()["id"]

    db = session_local()
    try:
        attempt = db.scalar(select(LabAttemptSession).where(LabAttemptSession.id == attempt_id))
        assert attempt is not None
        attempt.lab_attempt_status = "completed"
        db.commit()
    finally:
        db.close()

    response = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-mcq", "response_payload_json": {"selected_option_id": "opt-a"}},
    )

    assert response.status_code == 409


def test_repeated_submissions_use_best_score_per_exercise(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_mcq_exercise(session_local=session_local, lab_id=lab_id, is_required=False)

    attempt_response = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers)
    attempt_id = attempt_response.json()["id"]

    first_response = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-mcq", "response_payload_json": {"selected_option_id": "opt-a"}},
    )
    second_response = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-mcq", "response_payload_json": {"selected_option_id": "opt-a"}},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["session"]["total_score_awarded"] == 10
    assert second_response.json()["session"]["total_score_awarded"] == 10


def test_submit_rejects_unsupported_exercise_type(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_mcq_exercise(session_local=session_local, lab_id=lab_id, exercise_id="exercise-unsupported", exercise_type="code")

    attempt_response = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers)
    attempt_id = attempt_response.json()["id"]

    response = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-unsupported", "response_payload_json": {"selected_option_id": "opt-a"}},
    )

    assert response.status_code == 422


def test_submit_fill_blank_all_correct(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_exercise(
        session_local=session_local,
        lab_id=lab_id,
        exercise_id="exercise-fill-1",
        exercise_type="fill_blank",
        metadata_json='{"correct_answers":["output","high"]}',
    )

    attempt_id = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers).json()["id"]
    response = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-fill-1", "response_payload_json": {"answers": ["output", "high"]}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_correct"] is True
    assert body["score_awarded"] == 10


def test_submit_fill_blank_partially_correct(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_exercise(
        session_local=session_local,
        lab_id=lab_id,
        exercise_id="exercise-fill-2",
        exercise_type="fill_blank",
        metadata_json='{"correct_answers":["output","high"]}',
        max_score=9,
    )

    attempt_id = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers).json()["id"]
    response = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-fill-2", "response_payload_json": {"answers": ["output", "low"]}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_correct"] is False
    assert body["score_awarded"] == 4
    assert "[1]" in body["feedback"]


def test_submit_fill_blank_all_incorrect(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_exercise(
        session_local=session_local,
        lab_id=lab_id,
        exercise_id="exercise-fill-3",
        exercise_type="fill_blank",
        metadata_json='{"correct_answers":["output","high"]}',
    )

    attempt_id = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers).json()["id"]
    response = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-fill-3", "response_payload_json": {"answers": ["input", "low"]}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_correct"] is False
    assert body["score_awarded"] == 0
    assert "[0, 1]" in body["feedback"]


def test_submit_fill_blank_normalization_case_and_spacing(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_exercise(
        session_local=session_local,
        lab_id=lab_id,
        exercise_id="exercise-fill-4",
        exercise_type="fill_blank",
        metadata_json='{"correct_answers":["Output","HIGH"]}',
    )

    attempt_id = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers).json()["id"]
    response = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-fill-4", "response_payload_json": {"answers": {"0": "  out put  ", "1": " high "}}},
    )

    assert response.status_code == 200
    assert response.json()["is_correct"] is True


def test_submit_short_text_correct_keyword_match(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_exercise(
        session_local=session_local,
        lab_id=lab_id,
        exercise_id="exercise-short-1",
        exercise_type="short_text",
        metadata_json='{"accepted_answers":["limit current","protect led"]}',
    )

    attempt_id = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers).json()["id"]
    response = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={
            "exercise_id": "exercise-short-1",
            "response_payload_json": {"answer": "It helps LIMIT CURRENT to keep hardware safe."},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_correct"] is True
    assert body["score_awarded"] == 10


def test_submit_short_text_incorrect_response(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_exercise(
        session_local=session_local,
        lab_id=lab_id,
        exercise_id="exercise-short-2",
        exercise_type="short_text",
        metadata_json='{"accepted_answers":["limit current","protect led"]}',
    )

    attempt_id = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers).json()["id"]
    response = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-short-2", "response_payload_json": {"answer": "It makes the LED brighter."}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_correct"] is False
    assert body["score_awarded"] == 0


def test_submit_short_text_respects_min_matches(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_exercise(
        session_local=session_local,
        lab_id=lab_id,
        exercise_id="exercise-short-3",
        exercise_type="short_text",
        metadata_json='{"accepted_answers":["limit current","protect led","protect gpio"],"min_matches":2}',
    )

    attempt_id = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers).json()["id"]
    fail_response = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-short-3", "response_payload_json": {"answer": "It can limit current."}},
    )
    pass_response = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={
            "exercise_id": "exercise-short-3",
            "response_payload_json": {"answer": "It can limit current and protect LED circuits."},
        },
    )

    assert fail_response.status_code == 200
    assert fail_response.json()["is_correct"] is False
    assert pass_response.status_code == 200
    assert pass_response.json()["is_correct"] is True


def test_submit_rejects_malformed_fill_blank_metadata(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_exercise(
        session_local=session_local,
        lab_id=lab_id,
        exercise_id="exercise-fill-invalid",
        exercise_type="fill_blank",
        metadata_json='{"foo":["bar"]}',
    )

    attempt_id = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers).json()["id"]
    response = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-fill-invalid", "response_payload_json": {"answers": ["bar"]}},
    )

    assert response.status_code == 422


def test_submit_auto_completes_lab_when_all_required_exercises_are_correct(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_mcq_exercise(session_local=session_local, lab_id=lab_id, exercise_id="exercise-req-1")
    _create_mcq_exercise(session_local=session_local, lab_id=lab_id, exercise_id="exercise-req-2")

    attempt_id = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers).json()["id"]
    first_submit = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-req-1", "response_payload_json": {"selected_option_id": "opt-a"}},
    )
    second_submit = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-req-2", "response_payload_json": {"selected_option_id": "opt-a"}},
    )

    assert first_submit.status_code == 200
    assert second_submit.status_code == 200
    assert second_submit.json()["session"]["required_exercises_correct"] == 2
    assert second_submit.json()["session"]["required_exercises_total"] == 2

    progress_list = client.get("/api/v1/me/lab-progress", headers=headers)
    assert progress_list.status_code == 200
    lab_progress = next(item for item in progress_list.json() if item["lab_id"] == lab_id)
    assert lab_progress["status"] == "completed"
    assert lab_progress["completed_at"] is not None


def test_submit_does_not_auto_complete_if_one_required_exercise_is_incorrect(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_mcq_exercise(session_local=session_local, lab_id=lab_id, exercise_id="exercise-req-a")
    _create_mcq_exercise(session_local=session_local, lab_id=lab_id, exercise_id="exercise-req-b")

    attempt_id = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers).json()["id"]
    correct_submit = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-req-a", "response_payload_json": {"selected_option_id": "opt-a"}},
    )
    incorrect_submit = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-req-b", "response_payload_json": {"selected_option_id": "opt-b"}},
    )

    assert correct_submit.status_code == 200
    assert incorrect_submit.status_code == 200
    assert incorrect_submit.json()["session"]["required_exercises_correct"] == 1
    assert incorrect_submit.json()["session"]["required_exercises_total"] == 2

    progress_list = client.get("/api/v1/me/lab-progress", headers=headers)
    assert progress_list.status_code == 200
    lab_progress = next(item for item in progress_list.json() if item["lab_id"] == lab_id)
    assert lab_progress["status"] == "in_progress"
    assert lab_progress["completed_at"] is None


def test_submit_partial_completion_stays_in_progress(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_mcq_exercise(session_local=session_local, lab_id=lab_id, exercise_id="exercise-only-one-correct")
    _create_mcq_exercise(session_local=session_local, lab_id=lab_id, exercise_id="exercise-not-answered")

    attempt_id = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers).json()["id"]
    response = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-only-one-correct", "response_payload_json": {"selected_option_id": "opt-a"}},
    )

    assert response.status_code == 200
    assert response.json()["session"]["required_exercises_correct"] == 1
    assert response.json()["session"]["required_exercises_total"] == 2

    progress_list = client.get("/api/v1/me/lab-progress", headers=headers)
    assert progress_list.status_code == 200
    lab_progress = next(item for item in progress_list.json() if item["lab_id"] == lab_id)
    assert lab_progress["status"] == "in_progress"


def test_submit_idempotent_completion_does_not_overwrite_completed_at_timestamp(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_mcq_exercise(session_local=session_local, lab_id=lab_id, exercise_id="exercise-idem-1")
    _create_mcq_exercise(session_local=session_local, lab_id=lab_id, exercise_id="exercise-idem-2")

    attempt_id = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers).json()["id"]
    client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-idem-1", "response_payload_json": {"selected_option_id": "opt-a"}},
    )
    complete_submit = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-idem-2", "response_payload_json": {"selected_option_id": "opt-a"}},
    )
    assert complete_submit.status_code == 200

    first_progress = client.get("/api/v1/me/lab-progress", headers=headers)
    assert first_progress.status_code == 200
    first_lab_progress = next(item for item in first_progress.json() if item["lab_id"] == lab_id)
    first_status = first_lab_progress["status"]
    first_completed_at = first_lab_progress["completed_at"]

    repeated_complete = client.post(f"/api/v1/labs/{lab_id}/complete", headers=headers)
    assert repeated_complete.status_code == 200

    second_progress = client.get("/api/v1/me/lab-progress", headers=headers)
    assert second_progress.status_code == 200
    second_lab_progress = next(item for item in second_progress.json() if item["lab_id"] == lab_id)
    second_status = second_lab_progress["status"]
    second_completed_at = second_lab_progress["completed_at"]
    assert first_status == "completed"
    assert second_status == "completed"
    assert first_completed_at is not None
    assert second_completed_at == first_completed_at


def test_reopen_then_new_attempt_can_auto_complete_again(test_context):
    client = test_context["client"]
    session_local = test_context["session_local"]
    headers = _auth_headers(client)
    lab_id = str(INITIAL_LABS[0]["id"])
    _create_mcq_exercise(session_local=session_local, lab_id=lab_id, exercise_id="exercise-reopen-1")
    _create_mcq_exercise(session_local=session_local, lab_id=lab_id, exercise_id="exercise-reopen-2")

    first_attempt_id = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers).json()["id"]
    client.post(
        f"/api/v1/labs/{lab_id}/attempts/{first_attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-reopen-1", "response_payload_json": {"selected_option_id": "opt-a"}},
    )
    client.post(
        f"/api/v1/labs/{lab_id}/attempts/{first_attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-reopen-2", "response_payload_json": {"selected_option_id": "opt-a"}},
    )

    reopen_response = client.post(f"/api/v1/labs/{lab_id}/reopen", headers=headers)
    assert reopen_response.status_code == 200
    assert reopen_response.json()["status"] == "in_progress"

    second_attempt = client.post(f"/api/v1/labs/{lab_id}/attempts", headers=headers)
    assert second_attempt.status_code == 200
    assert second_attempt.json()["attempt_number"] == 2
    second_attempt_id = second_attempt.json()["id"]

    second_submit = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{second_attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-reopen-1", "response_payload_json": {"selected_option_id": "opt-a"}},
    )
    assert second_submit.status_code == 200
    progress_after_partial = client.get("/api/v1/me/lab-progress", headers=headers).json()
    lab_progress_partial = next(item for item in progress_after_partial if item["lab_id"] == lab_id)
    assert lab_progress_partial["status"] == "in_progress"

    final_submit = client.post(
        f"/api/v1/labs/{lab_id}/attempts/{second_attempt_id}/submit",
        headers=headers,
        json={"exercise_id": "exercise-reopen-2", "response_payload_json": {"selected_option_id": "opt-a"}},
    )
    assert final_submit.status_code == 200
    progress_after_complete = client.get("/api/v1/me/lab-progress", headers=headers).json()
    lab_progress_complete = next(item for item in progress_after_complete if item["lab_id"] == lab_id)
    assert lab_progress_complete["status"] == "completed"
