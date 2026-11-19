import logging
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.router import router as auth_router
from app.modules.catalog.router import router as catalog_router
from app.modules.listings.router import router as listings_router
from app.modules.offers.router import router as offers_router
from app.modules.orders.router import router as orders_router
from app.modules.stats.router import router as stats_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="WasteConnect API",
    description="Recyclable-waste marketplace for Pune",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        content = {
            "code": exc.detail.get("code", "ERROR"),
            "detail": exc.detail.get("detail", "An error occurred"),
        }
    else:
        content = {
            "code": "ERROR",
            "detail": str(exc.detail),
        }
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = [
        {"field": " -> ".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": "VALIDATION_ERROR",
            "detail": "Input validation failed",
            "errors": errors,
        },
    )


# Include Routers
app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(listings_router)
app.include_router(offers_router)
app.include_router(orders_router)
app.include_router(stats_router)


# Health checks
@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
def health_check() -> dict[str, str]:
    """Health check endpoint returning system status."""
    return {"status": "ok"}


@app.get("/health/db", tags=["Health"])
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


# Static files and frontend serving
_STATIC_DIR = Path(__file__).resolve().parent / "static"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
def serve_spa() -> Any:
    index_file = _STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "WasteConnect API is running. Build frontend in backend/app/static."}
