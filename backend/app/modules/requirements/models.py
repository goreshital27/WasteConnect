from decimal import Decimal
from uuid import UUID

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.auth.models import User
from app.modules.catalog.models import WasteCategory
from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Requirement(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "requirements"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'closed')",
            name="ck_requirements_status",
        ),
    )

    buyer_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("waste_categories.id"),
        nullable=False,
        index=True,
    )
    quantity_kg: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    max_price_per_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)

    buyer: Mapped[User] = relationship("User", lazy="joined")
    category: Mapped[WasteCategory] = relationship("WasteCategory", lazy="joined")
