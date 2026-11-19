import pytest
from app.core.config import Settings


def test_config_success_when_all_variables_present() -> None:
    """Settings loads successfully when all required parameters are provided."""
    settings = Settings.load(
        ENVIRONMENT="development",
        DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/wasteconnect",
        DIRECT_DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/wasteconnect",
        SECRET_KEY="super-secret-key-123456",
        _env_file=None,
    )
    assert settings.ENVIRONMENT == "development"
    assert "postgresql+psycopg" in settings.DATABASE_URL
    assert settings.SECRET_KEY == "super-secret-key-123456"


def test_config_fails_clearly_when_variable_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings fails clearly when a required variable is missing."""
    monkeypatch.delenv("DIRECT_DATABASE_URL", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    with pytest.raises(ValueError) as exc_info:
        Settings.load(
            ENVIRONMENT="development",
            DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/wasteconnect",
            # DIRECT_DATABASE_URL and SECRET_KEY intentionally missing
            _env_file=None,
        )

    error_msg = str(exc_info.value)
    assert "Configuration error: missing required environment variable(s)" in error_msg
    assert "DIRECT_DATABASE_URL" in error_msg or "SECRET_KEY" in error_msg


def test_config_error_never_leaks_secret_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """Config error messages must never contain secret values."""
    monkeypatch.delenv("DIRECT_DATABASE_URL", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    canary_secret = "my-ultra-confidential-secret-value-never-leak"
    with pytest.raises(ValueError) as exc_info:
        Settings.load(
            ENVIRONMENT="development",
            SECRET_KEY=canary_secret,
            # DATABASE_URL missing
            _env_file=None,
        )

    error_msg = str(exc_info.value)
    assert canary_secret not in error_msg
    assert "DATABASE_URL" in error_msg
