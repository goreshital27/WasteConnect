from unittest.mock import MagicMock

from app.core.database import get_db
from app.main import app
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    """GET /health must return HTTP 200 with {'status': 'ok'}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_db_up(client: TestClient) -> None:
    """GET /health/db must return HTTP 200 with {'database': 'up'} when DB succeeds."""
    mock_db = MagicMock()
    mock_db.execute.return_value = None

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/health/db")
        assert response.status_code == 200
        assert response.json() == {"database": "up"}
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_health_db_down(client: TestClient) -> None:
    """GET /health/db must return HTTP 503 with {'database': 'down'} and no leaked details."""
    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("Connection refused / database error")

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/health/db")
        assert response.status_code == 503
        assert response.json() == {"database": "down"}
        # Ensure no sensitive error strings leak in the body
        assert "Connection refused" not in response.text
    finally:
        app.dependency_overrides.pop(get_db, None)
