from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin
from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

VALID_ROLES = ("individual", "reseller", "aggregator", "recycler", "processor", "business")


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('individual', 'reseller', 'aggregator', 'recycler', 'processor', 'business')",
            name="ck_users_role",
        ),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    area: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
