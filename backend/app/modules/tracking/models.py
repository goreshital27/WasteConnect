from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.core.database import Base, UUIDPrimaryKeyMixin
from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column


class TrackingPosition(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "tracking_positions"

    order_id: Mapped[UUID] = mapped_column(
        ForeignKey("orders.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    lat: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    lng: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
