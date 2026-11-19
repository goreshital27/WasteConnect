from typing import Annotated, Any

from app.core.database import get_db
from app.modules.catalog.schemas import CategoryResponse
from app.modules.catalog.service import CatalogService
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

router = APIRouter(tags=["Catalog"])


@router.get(
    "/categories",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def list_categories(
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    categories = CatalogService.get_active_categories(db)
    return {
        "code": "SUCCESS",
        "data": [CategoryResponse.model_validate(c).model_dump(mode="json") for c in categories],
    }
