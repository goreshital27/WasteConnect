from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin
from sqlalchemy import Boolean, CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class WasteCategory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "waste_categories"
    __table_args__ = (
        CheckConstraint(
            "stream IN ('dry', 'wet')",
            name="ck_waste_categories_stream",
        ),
    )

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="kg", nullable=False)
    stream: Mapped[str] = mapped_column(String(10), default="dry", nullable=False)
    allows_zero_or_negative_price: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    expiry_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
