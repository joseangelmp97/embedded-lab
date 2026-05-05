from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.modules.labs.services.lab_service import seed_initial_labs
from app.modules.paths.services.path_service import assign_labs_to_paths, seed_initial_paths
from app.modules.users.models.user import User
from app.shared.db.base import Base
from app.shared.db.dependencies import get_db
from app.shared.db.session import _apply_sqlite_compatibility_fixes


@pytest.fixture
def legacy_client(tmp_path):
    db_file = tmp_path / "legacy_lab_progress.db"
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

    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS lab_progress"))
        connection.execute(
            text(
                """
                CREATE TABLE lab_progress (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    lab_id VARCHAR(100) NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    started_at DATETIME,
                    completed_at DATETIME,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_lab_progress_user_lab UNIQUE (user_id, lab_id),
                    FOREIGN KEY(user_id) REFERENCES users (id),
                    FOREIGN KEY(lab_id) REFERENCES labs (id)
                )
                """,
            ),
        )

    _apply_sqlite_compatibility_fixes(target_engine=engine)

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
        yield test_client, testing_session_local

    app.dependency_overrides.clear()
    engine.dispose()


def _auth_headers(client: TestClient) -> dict[str, str]:
    payload = {
        "email": f"legacy-progress-{uuid4().hex}@example.com",
        "password": "StrongPassword123!",
    }
    register_response = client.post("/api/v1/auth/register", json=payload)
    login_response = client.post("/api/v1/auth/login", json=payload)

    assert register_response.status_code == 201
    assert login_response.status_code == 200

    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def test_legacy_sqlite_table_upgraded_and_progress_endpoints_work(legacy_client):
    client, testing_session_local = legacy_client
    headers = _auth_headers(client)

    response_path_progress = client.get("/api/v1/me/path-progress", headers=headers)
    response_lab_progress = client.get("/api/v1/me/lab-progress", headers=headers)

    assert response_path_progress.status_code == 200
    assert response_lab_progress.status_code == 200

    db = testing_session_local()
    try:
        columns = [row[1] for row in db.execute(text("PRAGMA table_info('lab_progress')")).all()]
    finally:
        db.close()

    assert "completion_source" in columns


def test_null_completion_source_does_not_unlock_next_lab(legacy_client):
    client, testing_session_local = legacy_client
    headers = _auth_headers(client)

    user_lookup_db = testing_session_local()
    try:
        user_id = user_lookup_db.query(User.id).order_by(User.created_at.desc()).first()[0]
    finally:
        user_lookup_db.close()

    db = testing_session_local()
    try:
        db.execute(
            text(
                """
                INSERT INTO lab_progress (id, user_id, lab_id, status, completion_source)
                VALUES (:id, :user_id, :lab_id, 'completed', NULL)
                """,
            ),
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "lab_id": "digital-logic-voltage-levels",
            },
        )
        db.commit()
    finally:
        db.close()

    response = client.post("/api/v1/labs/gpio-led-basics/start", headers=headers)

    assert response.status_code == 403
    assert "Lab is locked" in response.json()["detail"]


def test_evaluated_completion_source_unlocks_next_lab(legacy_client):
    client, testing_session_local = legacy_client
    headers = _auth_headers(client)

    user_lookup_db = testing_session_local()
    try:
        user_id = user_lookup_db.query(User.id).order_by(User.created_at.desc()).first()[0]
    finally:
        user_lookup_db.close()

    db = testing_session_local()
    try:
        db.execute(
            text(
                """
                INSERT INTO lab_progress (id, user_id, lab_id, status, completion_source)
                VALUES (:id, :user_id, :lab_id, 'completed', 'evaluation')
                """,
            ),
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "lab_id": "digital-logic-voltage-levels",
            },
        )
        db.commit()
    finally:
        db.close()

    response = client.post("/api/v1/labs/gpio-led-basics/start", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
