from uuid import UUID

from app.modules.catalog.models import WasteCategory
from sqlalchemy import select
from sqlalchemy.orm import Session


class CatalogService:
    @staticmethod
    def get_active_categories(db: Session) -> list[WasteCategory]:
        return list(
            db.scalars(
                select(WasteCategory)
                .where(WasteCategory.is_active.is_(True))
                .order_by(WasteCategory.name)
            ).all()
        )

    @staticmethod
    def get_category_by_id(db: Session, category_id: UUID) -> WasteCategory | None:
        return db.scalar(select(WasteCategory).where(WasteCategory.id == category_id))

    @staticmethod
    def get_category_by_code(db: Session, code: str) -> WasteCategory | None:
        return db.scalar(select(WasteCategory).where(WasteCategory.code == code))
