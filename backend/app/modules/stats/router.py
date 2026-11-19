from typing import Annotated, Any

from app.core.database import get_db
from app.modules.stats.service import StatsService
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get(
    "/rate-card",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def get_rate_card(
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    cards = StatsService.get_rate_card(db)
    return {
        "code": "SUCCESS",
        "data": cards,
    }


@router.get(
    "/impact",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def get_impact(
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    impact = StatsService.get_impact_stats(db)
    return {
        "code": "SUCCESS",
        "data": impact,
    }
