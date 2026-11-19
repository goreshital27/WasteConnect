from decimal import Decimal
from typing import Any
from uuid import UUID

from app.modules.orders.models import Order, OrderStatusHistory, WeightRecord
from app.modules.orders.schemas import WeightRecordCreateRequest
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

VALID_TRANSITIONS: dict[str, list[str]] = {
    "confirmed": ["collected", "cancelled"],
    "collected": ["delivered"],
    "delivered": ["completed"],
    "completed": [],
    "cancelled": [],
}


class OrderService:
    @staticmethod
    def get_orders_for_user(db: Session, user_id: UUID) -> list[Order]:
        stmt = (
            select(Order)
            .where((Order.seller_id == user_id) | (Order.buyer_id == user_id))
            .order_by(Order.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_order_by_id(
        db: Session,
        order_id: UUID,
        user_id: UUID | None = None,
    ) -> Order:
        order = db.scalar(select(Order).where(Order.id == order_id))
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ORDER_NOT_FOUND", "detail": "Order not found"},
            )
        if user_id and order.seller_id != user_id and order.buyer_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "detail": "Access to this order is forbidden"},
            )
        return order

    @staticmethod
    def record_weight(
        db: Session,
        order_id: UUID,
        user_id: UUID,
        req: WeightRecordCreateRequest,
    ) -> WeightRecord:
        order = OrderService.get_order_by_id(db, order_id, user_id)

        if order.status in ("completed", "cancelled"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "ORDER_CLOSED",
                    "detail": f"Cannot record weight for order in '{order.status}' status",
                },
            )

        # Ensure correct timing for stage
        if req.stage == "collection" and order.status not in ("confirmed", "collected"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_STAGE_TIMING",
                    "detail": (
                        "Collection weight can only be recorded when "
                        "order is confirmed or collected"
                    ),
                },
            )
        if req.stage == "delivery" and order.status not in ("collected", "delivered"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_STAGE_TIMING",
                    "detail": "Delivery weight can only be recorded after order is collected",
                },
            )

        # Check existing record for this stage
        existing = db.scalar(
            select(WeightRecord).where(
                WeightRecord.order_id == order_id,
                WeightRecord.stage == req.stage,
            )
        )
        if existing:
            existing.weight_kg = req.weight_kg
            db.commit()
            db.refresh(existing)
            return existing

        record = WeightRecord(
            order_id=order_id,
            stage=req.stage,
            weight_kg=req.weight_kg,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def transition_order_status(
        db: Session,
        order_id: UUID,
        user_id: UUID,
        target_status: str,
    ) -> Order:
        order = OrderService.get_order_by_id(db, order_id, user_id)

        # Only the buyer moves it forward (or cancels while confirmed)
        if order.buyer_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "BUYER_ACTION_ONLY",
                    "detail": "Only the buyer can transition order status",
                },
            )

        current_status = order.status
        allowed_targets = VALID_TRANSITIONS.get(current_status, [])
        if target_status not in allowed_targets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_STATE_TRANSITION",
                    "detail": (
                        f"Cannot transition order from '{current_status}' "
                        f"to '{target_status}'"
                    ),
                },
            )

        # Validation checks for state transitions
        if target_status == "collected":
            has_collection_weight = any(w.stage == "collection" for w in order.weight_records)
            if not has_collection_weight:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "COLLECTION_WEIGHT_REQUIRED",
                        "detail": (
                            "Weight must be recorded at collection before moving to collected"
                        ),
                    },
                )

        if target_status == "delivered":
            has_delivery_weight = any(w.stage == "delivery" for w in order.weight_records)
            if not has_delivery_weight:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "DELIVERY_WEIGHT_REQUIRED",
                        "detail": "Weight must be recorded at delivery before moving to delivered",
                    },
                )

        # Apply transition
        order.status = target_status

        history = OrderStatusHistory(
            order_id=order.id,
            from_status=current_status,
            to_status=target_status,
            changed_by_id=user_id,
        )
        db.add(history)

        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def enrich_order_dict(order: Order) -> dict[str, Any]:
        """Compute collection weight, delivery weight, and difference."""
        collection_w: Decimal | None = None
        delivery_w: Decimal | None = None
        for w in order.weight_records:
            if w.stage == "collection":
                collection_w = w.weight_kg
            elif w.stage == "delivery":
                delivery_w = w.weight_kg

        diff_kg: Decimal | None = None
        if collection_w is not None and delivery_w is not None:
            diff_kg = collection_w - delivery_w

        data = {
            "id": order.id,
            "offer_id": order.offer_id,
            "seller_id": order.seller_id,
            "buyer_id": order.buyer_id,
            "status": order.status,
            "created_at": order.created_at,
            "seller": order.seller,
            "buyer": order.buyer,
            "offer": order.offer,
            "weight_records": order.weight_records,
            "status_history": order.status_history,
            "collection_weight_kg": collection_w,
            "delivery_weight_kg": delivery_w,
            "weight_difference_kg": diff_kg,
        }
        return data
