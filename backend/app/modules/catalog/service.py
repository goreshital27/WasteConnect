from uuid import UUID

from app.modules.catalog.models import WasteCategory
from sqlalchemy import select
from sqlalchemy.orm import Session


class CatalogService:
    @staticmethod
    def get_active_categories(db: Session, stream: str | None = None) -> list[WasteCategory]:
        stmt = select(WasteCategory).where(WasteCategory.is_active.is_(True))
        if stream:
            stmt = stmt.where(WasteCategory.stream == stream.lower().strip())
        stmt = stmt.order_by(WasteCategory.name)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_category_by_id(db: Session, category_id: UUID) -> WasteCategory | None:
        return db.scalar(select(WasteCategory).where(WasteCategory.id == category_id))

    @staticmethod
    def get_category_by_code(db: Session, code: str) -> WasteCategory | None:
        return db.scalar(select(WasteCategory).where(WasteCategory.code == code))
