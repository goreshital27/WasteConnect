from typing import Annotated, Any
from uuid import UUID

from app.core.database import get_db
from app.core.permissions.auth import get_current_user
from app.modules.auth.models import User
from app.modules.tracking.schemas import TrackingPositionCreate, TrackingPositionResponse
from app.modules.tracking.service import TrackingService
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

router = APIRouter(tags=["Tracking"])


@router.post(
    "/tracking/orders/{order_id}/position",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
@router.post(
    "/orders/{order_id}/tracking",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def record_order_position(
    order_id: UUID,
    payload: TrackingPositionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    pos = TrackingService.record_position(
        db=db,
        order_id=order_id,
        user_id=current_user.id,
        lat=payload.lat,
        lng=payload.lng,
    )
    return {
        "code": "SUCCESS",
        "data": TrackingPositionResponse.model_validate(pos).model_dump(mode="json"),
    }


@router.get(
    "/tracking/orders/{order_id}/position",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
@router.get(
    "/orders/{order_id}/tracking",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def get_order_position(
    order_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    pos = TrackingService.get_position(
        db=db,
        order_id=order_id,
        user_id=current_user.id,
    )
    return {
        "code": "SUCCESS",
        "data": (
            TrackingPositionResponse.model_validate(pos).model_dump(mode="json") if pos else None
        ),
    }
