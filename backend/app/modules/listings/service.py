from decimal import Decimal
from uuid import UUID

from app.modules.catalog.models import WasteCategory
from app.modules.listings.models import Listing
from app.modules.listings.schemas import ListingCreateRequest
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session


class ListingService:
    @staticmethod
    def create_listing(db: Session, seller_id: UUID, req: ListingCreateRequest) -> Listing:
        category = db.scalar(select(WasteCategory).where(WasteCategory.id == req.category_id))
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CATEGORY_NOT_FOUND", "detail": "Waste category not found"},
            )
        if not category.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "CATEGORY_INACTIVE", "detail": "Waste category is inactive"},
            )

        listing = Listing(
            seller_id=seller_id,
            category_id=req.category_id,
            title=req.title.strip(),
            quantity_kg=req.quantity_kg,
            price_per_kg=req.price_per_kg,
            is_negotiable=req.is_negotiable,
            area=req.area.strip(),
            pincode=req.pincode.strip(),
            status="open",
        )
        db.add(listing)
        db.commit()
        db.refresh(listing)
        return listing

    @staticmethod
    def get_listings(
        db: Session,
        category_id: UUID | None = None,
        category_code: str | None = None,
        pincode: str | None = None,
        min_quantity: Decimal | None = None,
        status_filter: str | None = "open",
    ) -> list[Listing]:
        stmt = select(Listing)
        if status_filter:
            stmt = stmt.where(Listing.status == status_filter)
        if category_id:
            stmt = stmt.where(Listing.category_id == category_id)
        if category_code:
            stmt = stmt.join(Listing.category).where(WasteCategory.code == category_code.lower())
        if pincode:
            stmt = stmt.where(Listing.pincode == pincode.strip())
        if min_quantity is not None and min_quantity > 0:
            stmt = stmt.where(Listing.quantity_kg >= min_quantity)

        stmt = stmt.order_by(Listing.created_at.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_listing_by_id(db: Session, listing_id: UUID) -> Listing | None:
        return db.scalar(select(Listing).where(Listing.id == listing_id))

    @staticmethod
    def cancel_listing(db: Session, listing_id: UUID, user_id: UUID) -> Listing:
        listing = db.scalar(select(Listing).where(Listing.id == listing_id))
        if not listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "LISTING_NOT_FOUND", "detail": "Listing not found"},
            )
        if listing.seller_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "detail": "Only the seller can cancel this listing"},
            )
        if listing.status != "open":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_STATE",
                    "detail": f"Cannot cancel listing in '{listing.status}' status",
                },
            )

        listing.status = "cancelled"
        db.commit()
        db.refresh(listing)
        return listing

    @staticmethod
    def get_seller_listings(db: Session, seller_id: UUID) -> list[Listing]:
        return list(
            db.scalars(
                select(Listing)
                .where(Listing.seller_id == seller_id)
                .order_by(Listing.created_at.desc())
            ).all()
        )
