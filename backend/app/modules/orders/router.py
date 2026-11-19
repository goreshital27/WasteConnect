from typing import Annotated, Any
from uuid import UUID

from app.core.database import get_db
from app.core.permissions.auth import get_current_user
from app.modules.auth.models import User
from app.modules.orders.schemas import (
    OrderResponse,
    OrderStatusTransitionRequest,
    WeightRecordCreateRequest,
    WeightRecordResponse,
)
from app.modules.orders.service import OrderService
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

router = APIRouter(tags=["Orders"])


@router.get(
    "/orders",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def list_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    orders = OrderService.get_orders_for_user(db, current_user.id)
    result = []
    for o in orders:
        enriched = OrderService.enrich_order_dict(o)
        result.append(OrderResponse.model_validate(enriched).model_dump(mode="json"))
    return {
        "code": "SUCCESS",
        "data": result,
    }


@router.get(
    "/orders/{order_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def get_order(
    order_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    order = OrderService.get_order_by_id(db, order_id, current_user.id)
    enriched = OrderService.enrich_order_dict(order)
    return {
        "code": "SUCCESS",
        "data": OrderResponse.model_validate(enriched).model_dump(mode="json"),
    }


@router.post(
    "/orders/{order_id}/weights",
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, Any],
)
def record_weight(
    order_id: UUID,
    req: WeightRecordCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    record = OrderService.record_weight(db, order_id, current_user.id, req)
    return {
        "code": "SUCCESS",
        "data": WeightRecordResponse.model_validate(record).model_dump(mode="json"),
    }


@router.post(
    "/orders/{order_id}/transition",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def transition_order(
    order_id: UUID,
    req: OrderStatusTransitionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    order = OrderService.transition_order_status(db, order_id, current_user.id, req.target_status)
    enriched = OrderService.enrich_order_dict(order)
    return {
        "code": "SUCCESS",
        "data": OrderResponse.model_validate(enriched).model_dump(mode="json"),
    }
