from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.modules.catalog.models import WasteCategory
from app.modules.listings.models import Listing
from app.modules.listings.schemas import ListingCreateRequest
from app.modules.matching.service import MatchingService
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

        # Price rule validation
        if not category.allows_zero_or_negative_price and req.price_per_kg <= Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "PRICE_MUST_BE_POSITIVE",
                    "detail": "Price per kg must be greater than zero for dry waste categories",
                },
            )

        # Expiry time computation
        now = datetime.now(UTC)
        expires_at = req.expires_at
        if not expires_at and category.stream == "wet" and category.expiry_hours:
            expires_at = now + timedelta(hours=category.expiry_hours)

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
            expires_at=expires_at,
        )
        db.add(listing)
        db.flush()

        # Match open requirements and notify buyers
        MatchingService.match_new_listing(db, listing)

        db.commit()
        db.refresh(listing)
        return listing

    @staticmethod
    def enrich_listing_dict(db: Session, listing: Listing) -> dict[str, Any]:
        now = datetime.now(UTC)
        is_expired = False
        if listing.expires_at:
            exp = listing.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=UTC)
            is_expired = exp <= now

        matches_count = MatchingService.count_matches_for_listing(db, listing)

        return {
            "id": listing.id,
            "seller_id": listing.seller_id,
            "category_id": listing.category_id,
            "title": listing.title,
            "quantity_kg": listing.quantity_kg,
            "price_per_kg": listing.price_per_kg,
            "is_negotiable": listing.is_negotiable,
            "area": listing.area,
            "pincode": listing.pincode,
            "status": listing.status,
            "expires_at": listing.expires_at,
            "is_expired": is_expired,
            "matches_count": matches_count,
            "created_at": listing.created_at,
            "seller": listing.seller,
            "category": listing.category,
        }

    @staticmethod
    def get_listings(
        db: Session,
        category_id: UUID | None = None,
        category_code: str | None = None,
        stream: str | None = None,
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
        if stream:
            stmt = stmt.join(Listing.category).where(WasteCategory.stream == stream.lower().strip())
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
