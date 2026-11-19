from decimal import Decimal
from uuid import UUID

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.auth.models import User
from app.modules.listings.models import Listing
from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Offer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "offers"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'accepted', 'rejected')",
            name="ck_offers_status",
        ),
    )

    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("listings.id"),
        nullable=False,
        index=True,
    )
    buyer_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    quantity_kg: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    price_per_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)

    listing: Mapped[Listing] = relationship("Listing", lazy="joined")
    buyer: Mapped[User] = relationship("User", lazy="joined")
