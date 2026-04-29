from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.modules.labs.services.lab_service import seed_initial_labs
from app.modules.paths.services.path_service import (
    INITIAL_PATHS,
    LAB_PATH_ASSIGNMENTS,
    assign_labs_to_paths,
    seed_initial_paths,
)
from app.modules.paths.services.path_module_service import (
    INITIAL_PATH_MODULES,
    assign_labs_to_modules,
    seed_initial_path_modules,
)
from app.shared.db.base import Base
from app.shared.db.dependencies import get_db


@pytest.fixture
def client(tmp_path) -> TestClient:
    db_file = tmp_path / "paths_api.db"
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
        seed_initial_path_modules(db=seed_db)
        seed_initial_labs(db=seed_db)
        assign_labs_to_paths(db=seed_db)
        assign_labs_to_modules(db=seed_db)
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
        "email": f"paths-{uuid4().hex}@example.com",
        "password": "StrongPassword123!",
    }
    register_response = client.post("/api/v1/auth/register", json=payload)
    login_response = client.post("/api/v1/auth/login", json=payload)

    assert register_response.status_code == 201
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def test_paths_list_returns_seeded_paths_for_authenticated_user(client: TestClient):
    token = _authenticate(client)

    response = client.get("/api/v1/paths", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == len(INITIAL_PATHS)
    assert [path["name"] for path in body] == [path["name"] for path in INITIAL_PATHS]


def test_path_labs_returns_labs_for_requested_path(client: TestClient):
    token = _authenticate(client)
    embedded_fundamentals_id = str(INITIAL_PATHS[0]["id"])

    response = client.get(
        f"/api/v1/paths/{embedded_fundamentals_id}/labs",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    expected_labs = [
        lab_id
        for lab_id, path_name in LAB_PATH_ASSIGNMENTS.items()
        if path_name == INITIAL_PATHS[0]["name"]
    ]
    assert [lab["id"] for lab in body] == expected_labs


def test_path_labs_returns_404_for_missing_path(client: TestClient):
    token = _authenticate(client)

    response = client.get(
        "/api/v1/paths/00000000-0000-4000-8000-000000000000/labs",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Path not found"


def test_paths_endpoints_require_authentication(client: TestClient):
    paths_response = client.get("/api/v1/paths")
    path_labs_response = client.get("/api/v1/paths/00000000-0000-4000-8000-000000000000/labs")
    path_modules_response = client.get("/api/v1/paths/00000000-0000-4000-8000-000000000000/modules")
    module_labs_response = client.get("/api/v1/modules/00000000-0000-4000-8000-000000000000/labs")

    assert paths_response.status_code == 401
    assert paths_response.json()["detail"] == "Not authenticated"
    assert path_labs_response.status_code == 401
    assert path_labs_response.json()["detail"] == "Not authenticated"
    assert path_modules_response.status_code == 401
    assert path_modules_response.json()["detail"] == "Not authenticated"
    assert module_labs_response.status_code == 401
    assert module_labs_response.json()["detail"] == "Not authenticated"


def test_path_modules_returns_modules_for_requested_path(client: TestClient):
    token = _authenticate(client)
    sensors_path_id = str(INITIAL_PATHS[1]["id"])

    response = client.get(
        f"/api/v1/paths/{sensors_path_id}/modules",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    expected_modules = [module for module in INITIAL_PATH_MODULES if module["path_id"] == sensors_path_id]
    assert [module["id"] for module in body] == [module["id"] for module in expected_modules]


def test_module_labs_returns_labs_for_requested_module(client: TestClient):
    token = _authenticate(client)
    input_reliability_module_id = INITIAL_PATH_MODULES[1]["id"]

    response = client.get(
        f"/api/v1/modules/{input_reliability_module_id}/labs",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert [lab["id"] for lab in body] == ["button-debounce-fundamentals"]


def test_module_labs_returns_404_for_missing_module(client: TestClient):
    token = _authenticate(client)

    response = client.get(
        "/api/v1/modules/00000000-0000-4000-8000-000000000000/labs",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Module not found"
