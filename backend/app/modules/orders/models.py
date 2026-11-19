from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.auth.models import User
from app.modules.offers.models import Offer
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Order(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "status IN ('confirmed', 'collected', 'delivered', 'completed', 'cancelled')",
            name="ck_orders_status",
        ),
    )

    offer_id: Mapped[UUID] = mapped_column(
        ForeignKey("offers.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    seller_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    buyer_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), default="confirmed", nullable=False)

    offer: Mapped[Offer] = relationship("Offer", lazy="joined")
    seller: Mapped[User] = relationship("User", foreign_keys=[seller_id], lazy="joined")
    buyer: Mapped[User] = relationship("User", foreign_keys=[buyer_id], lazy="joined")
    weight_records: Mapped[list["WeightRecord"]] = relationship(
        "WeightRecord",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="WeightRecord.created_at",
        lazy="selectin",
    )
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(
        "OrderStatusHistory",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderStatusHistory.created_at",
        lazy="selectin",
    )


class OrderStatusHistory(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "order_status_history"

    order_id: Mapped[UUID] = mapped_column(
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    order: Mapped[Order] = relationship("Order", back_populates="status_history")
    changed_by: Mapped[User] = relationship("User", lazy="joined")


class WeightRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "weight_records"
    __table_args__ = (
        CheckConstraint(
            "stage IN ('collection', 'delivery')",
            name="ck_weight_records_stage",
        ),
        UniqueConstraint("order_id", "stage", name="uq_weight_records_order_id_stage"),
    )

    order_id: Mapped[UUID] = mapped_column(
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )
    stage: Mapped[str] = mapped_column(String(20), nullable=False)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)

    order: Mapped[Order] = relationship("Order", back_populates="weight_records")
