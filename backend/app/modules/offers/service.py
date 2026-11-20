from datetime import UTC, datetime
from uuid import UUID

from app.modules.listings.models import Listing
from app.modules.offers.models import Offer
from app.modules.offers.schemas import OfferCreateRequest
from app.modules.orders.models import Order, OrderStatusHistory
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session


class OfferService:
    @staticmethod
    def create_offer(
        db: Session,
        listing_id: UUID,
        buyer_id: UUID,
        req: OfferCreateRequest,
    ) -> Offer:
        listing = db.scalar(select(Listing).where(Listing.id == listing_id))
        if not listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "LISTING_NOT_FOUND", "detail": "Listing not found"},
            )
        if listing.status != "open":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "LISTING_NOT_OPEN", "detail": "Listing is not open for offers"},
            )

        now = datetime.now(UTC)
        if listing.expires_at:
            exp = listing.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=UTC)
            if exp <= now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "LISTING_EXPIRED",
                        "detail": "Listing has expired and cannot receive offers",
                    },
                )

        if listing.seller_id == buyer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "SELF_OFFER_NOT_ALLOWED",
                    "detail": "Cannot make an offer on your own listing",
                },
            )

        offer = Offer(
            listing_id=listing_id,
            buyer_id=buyer_id,
            quantity_kg=req.quantity_kg,
            price_per_kg=req.price_per_kg,
            status="pending",
        )
        db.add(offer)
        db.commit()
        db.refresh(offer)
        return offer

    @staticmethod
    def get_received_offers(db: Session, seller_id: UUID) -> list[Offer]:
        stmt = (
            select(Offer)
            .join(Listing, Offer.listing_id == Listing.id)
            .where(Listing.seller_id == seller_id)
            .order_by(Offer.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_sent_offers(db: Session, buyer_id: UUID) -> list[Offer]:
        stmt = (
            select(Offer)
            .where(Offer.buyer_id == buyer_id)
            .order_by(Offer.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_offer_by_id(db: Session, offer_id: UUID) -> Offer | None:
        return db.scalar(select(Offer).where(Offer.id == offer_id))

    @staticmethod
    def accept_offer(db: Session, offer_id: UUID, user_id: UUID) -> tuple[Offer, Order]:
        offer = db.scalar(select(Offer).where(Offer.id == offer_id))
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "OFFER_NOT_FOUND", "detail": "Offer not found"},
            )
        if offer.listing.seller_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "detail": "Only the listing seller can accept this offer",
                },
            )
        if offer.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "OFFER_NOT_PENDING",
                    "detail": f"Offer is already '{offer.status}'",
                },
            )
        if offer.listing.status != "open":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "LISTING_NOT_OPEN", "detail": "Listing is no longer open"},
            )

        # Accept current offer
        offer.status = "accepted"

        # Mark listing sold
        offer.listing.status = "sold"

        # Reject all other pending offers on this listing
        db.execute(
            update(Offer)
            .where(
                Offer.listing_id == offer.listing_id,
                Offer.id != offer.id,
                Offer.status == "pending",
            )
            .values(status="rejected")
        )

        # Create confirmed order
        order = Order(
            offer_id=offer.id,
            seller_id=offer.listing.seller_id,
            buyer_id=offer.buyer_id,
            status="confirmed",
        )
        db.add(order)
        db.flush()

        history = OrderStatusHistory(
            order_id=order.id,
            from_status=None,
            to_status="confirmed",
            changed_by_id=user_id,
        )
        db.add(history)

        db.commit()
        db.refresh(offer)
        db.refresh(order)
        return offer, order

    @staticmethod
    def reject_offer(db: Session, offer_id: UUID, user_id: UUID) -> Offer:
        offer = db.scalar(select(Offer).where(Offer.id == offer_id))
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "OFFER_NOT_FOUND", "detail": "Offer not found"},
            )
        if offer.listing.seller_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "detail": "Only the listing seller can reject this offer",
                },
            )
        if offer.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "OFFER_NOT_PENDING",
                    "detail": f"Offer is already '{offer.status}'",
                },
            )

        offer.status = "rejected"
        db.commit()
        db.refresh(offer)
        return offer
