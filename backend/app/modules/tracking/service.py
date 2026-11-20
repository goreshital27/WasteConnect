from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.modules.orders.service import OrderService
from app.modules.tracking.models import TrackingPosition
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session


class TrackingService:
    @staticmethod
    def record_position(
        db: Session,
        order_id: UUID,
        user_id: UUID,
        lat: Decimal,
        lng: Decimal,
    ) -> TrackingPosition:
        order = OrderService.get_order_by_id(db, order_id)

        if order.buyer_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "detail": "Only the buyer can post tracking position for this order",
                },
            )

        if order.status != "collected":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_ORDER_STATUS",
                    "detail": (
                        f"Tracking position can only be posted when order status is 'collected', "
                        f"current status is '{order.status}'"
                    ),
                },
            )

        stmt = select(TrackingPosition).where(TrackingPosition.order_id == order_id)
        pos = db.scalar(stmt)
        if pos:
            pos.lat = lat
            pos.lng = lng
            pos.updated_at = datetime.now(UTC)
        else:
            pos = TrackingPosition(
                order_id=order_id,
                lat=lat,
                lng=lng,
            )
            db.add(pos)

        db.commit()
        db.refresh(pos)
        return pos

    @staticmethod
    def get_position(
        db: Session,
        order_id: UUID,
        user_id: UUID,
    ) -> TrackingPosition | None:
        order = OrderService.get_order_by_id(db, order_id)

        if order.seller_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "detail": "Only the seller can read tracking position for this order",
                },
            )

        if order.status != "collected":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_ORDER_STATUS",
                    "detail": (
                        f"Tracking position is only available when order status is 'collected', "
                        f"current status is '{order.status}'"
                    ),
                },
            )

        stmt = select(TrackingPosition).where(TrackingPosition.order_id == order_id)
        return db.scalar(stmt)
