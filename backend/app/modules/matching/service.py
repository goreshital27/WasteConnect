import uuid
from datetime import UTC, datetime

from app.modules.listings.models import Listing
from app.modules.notifications.models import Notification
from app.modules.requirements.models import Requirement
from sqlalchemy import DateTime, Uuid, bindparam, text
from sqlalchemy.orm import Session


class MatchingService:
    @staticmethod
    def match_new_listing(db: Session, listing: Listing) -> int:
        """Find open requirements matching category & pincode and notify buyers."""
        stmt = text(
            """
            SELECT id, buyer_id
            FROM requirements
            WHERE category_id = :category_id
              AND pincode = :pincode
              AND status = 'open'
              AND buyer_id != :seller_id
            """
        ).bindparams(
            bindparam("category_id", type_=Uuid(as_uuid=True)),
            bindparam("seller_id", type_=Uuid(as_uuid=True)),
        )
        matches = db.execute(
            stmt,
            {
                "category_id": listing.category_id,
                "pincode": listing.pincode,
                "seller_id": listing.seller_id,
            },
        ).fetchall()

        for row in matches:
            buyer_uuid = (
                row.buyer_id
                if isinstance(row.buyer_id, uuid.UUID)
                else uuid.UUID(str(row.buyer_id))
            )
            l_qty = float(listing.quantity_kg)
            l_price = float(listing.price_per_kg)
            notif = Notification(
                user_id=buyer_uuid,
                message=(
                    f"New match in {listing.pincode}: Listing '{listing.title}' "
                    f"({l_qty:.2f} kg @ ₹{l_price:.2f}/kg) "
                    "matches your open requirement."
                ),
            )
            db.add(notif)

        if matches:
            db.flush()
        return len(matches)

    @staticmethod
    def match_new_requirement(db: Session, req: Requirement) -> int:
        """Find open unexpired listings matching category & pincode and notify buyer."""
        now = datetime.now(UTC)
        stmt = text(
            """
            SELECT id, title, quantity_kg, price_per_kg, pincode
            FROM listings
            WHERE category_id = :category_id
              AND pincode = :pincode
              AND status = 'open'
              AND seller_id != :buyer_id
              AND (expires_at IS NULL OR expires_at > :now)
            """
        ).bindparams(
            bindparam("category_id", type_=Uuid(as_uuid=True)),
            bindparam("buyer_id", type_=Uuid(as_uuid=True)),
            bindparam("now", type_=DateTime(timezone=True)),
        )
        matches = db.execute(
            stmt,
            {
                "category_id": req.category_id,
                "pincode": req.pincode,
                "buyer_id": req.buyer_id,
                "now": now,
            },
        ).fetchall()

        for row in matches:
            buyer_uuid = (
                req.buyer_id
                if isinstance(req.buyer_id, uuid.UUID)
                else uuid.UUID(str(req.buyer_id))
            )
            notif = Notification(
                user_id=buyer_uuid,
                message=(
                    f"Match found in {row.pincode}: Listing '{row.title}' "
                    f"({float(row.quantity_kg):.2f} kg @ ₹{float(row.price_per_kg):.2f}/kg) "
                    "matches your requirement."
                ),
            )
            db.add(notif)

        if matches:
            db.flush()
        return len(matches)

    @staticmethod
    def count_matches_for_listing(db: Session, listing: Listing) -> int:
        """Count open requirements matching this listing's category and pincode."""
        stmt = text(
            """
            SELECT COUNT(*) AS cnt
            FROM requirements
            WHERE category_id = :category_id
              AND pincode = :pincode
              AND status = 'open'
            """
        ).bindparams(
            bindparam("category_id", type_=Uuid(as_uuid=True)),
        )
        val = db.execute(
            stmt,
            {
                "category_id": listing.category_id,
                "pincode": listing.pincode,
            },
        ).scalar()
        return int(val or 0)
