from decimal import Decimal
from uuid import UUID

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.auth.models import User
from app.modules.catalog.models import WasteCategory
from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Listing(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "listings"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'sold', 'cancelled')",
            name="ck_listings_status",
        ),
    )

    seller_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("waste_categories.id"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    quantity_kg: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    price_per_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_negotiable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    area: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)

    seller: Mapped[User] = relationship("User", lazy="joined")
    category: Mapped[WasteCategory] = relationship("WasteCategory", lazy="joined")
