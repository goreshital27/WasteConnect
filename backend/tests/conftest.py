import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

# Set default test environment variables before importing app
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://test_user:test_pass@localhost:5432/wasteconnect_test",
)
os.environ.setdefault(
    "DIRECT_DATABASE_URL",
    "postgresql+psycopg://test_user:test_pass@localhost:5432/wasteconnect_test",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-characters-long")

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> Generator[TestClient]:
    """Yield a FastAPI TestClient."""
    with TestClient(app) as test_client:
        yield test_client
