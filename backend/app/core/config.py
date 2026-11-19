from functools import lru_cache
from pathlib import Path

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_ENV_FILE = _REPO_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", str(_ENV_FILE)),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str
    DATABASE_URL: str
    DIRECT_DATABASE_URL: str
    SECRET_KEY: str

    @classmethod
    def load(cls, **kwargs) -> "Settings":
        try:
            return cls(**kwargs)
        except ValidationError as exc:
            missing = [
                str(err["loc"][0])
                for err in exc.errors()
                if err.get("type") == "missing"
            ]
            if missing:
                missing_str = ", ".join(missing)
                raise ValueError(
                    f"Configuration error: missing required environment variable(s): {missing_str}."
                    " Ensure these are set in your environment or .env file."
                ) from None
            error_fields = [str(err["loc"][0]) for err in exc.errors()]
            fields_str = ", ".join(error_fields)
            raise ValueError(
                f"Configuration error: invalid configuration for field(s): {fields_str}."
            ) from None


@lru_cache
def get_settings() -> Settings:
    return Settings.load()
