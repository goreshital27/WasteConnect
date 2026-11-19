import logging
from typing import Annotated, Any

from fastapi import Depends, FastAPI, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

logger = logging.getLogger(__name__)

app = FastAPI(
    title="WasteConnect API",
    description="Recyclable-waste marketplace API",
    version="0.1.0",
)


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check() -> dict[str, str]:
    """Health check endpoint returning system status."""
    return {"status": "ok"}


@app.get("/health/db")
def health_db_check(db: Annotated[Session, Depends(get_db)]) -> Any:
    """Database connectivity health check."""
    try:
        db.execute(text("SELECT 1"))
        return {"database": "up"}
    except Exception:
        logger.exception("Database health check failed")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"database": "down"},
        )
