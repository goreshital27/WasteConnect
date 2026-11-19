from decimal import Decimal
from typing import Any

from app.modules.catalog.models import WasteCategory
from app.modules.listings.models import Listing
from app.modules.orders.models import Order
from sqlalchemy import func, select
from sqlalchemy.orm import Session


class StatsService:
    @staticmethod
    def get_rate_card(db: Session) -> list[dict[str, Any]]:
        """Return min, avg, max price_per_kg per category for open listings."""
        categories = db.scalars(
            select(WasteCategory).where(WasteCategory.is_active.is_(True)).order_by(WasteCategory.name)
        ).all()

        # Query stats grouped by category_id
        stats_query = (
            select(
                Listing.category_id,
                func.min(Listing.price_per_kg).label("min_price"),
                func.avg(Listing.price_per_kg).label("avg_price"),
                func.max(Listing.price_per_kg).label("max_price"),
                func.count(Listing.id).label("listing_count"),
                func.sum(Listing.quantity_kg).label("total_quantity"),
            )
            .where(Listing.status == "open")
            .group_by(Listing.category_id)
        )
        stats_rows = {row.category_id: row for row in db.execute(stats_query)}

        result = []
        for cat in categories:
            row = stats_rows.get(cat.id)
            if row and row.listing_count > 0:
                min_p = Decimal(str(row.min_price)) if row.min_price is not None else None
                avg_p = (
                    Decimal(str(round(row.avg_price, 2)))
                    if row.avg_price is not None
                    else None
                )
                max_p = Decimal(str(row.max_price)) if row.max_price is not None else None
                tot_qty = (
                    Decimal(str(row.total_quantity))
                    if row.total_quantity is not None
                    else Decimal("0")
                )
                count = row.listing_count
            else:
                min_p, avg_p, max_p = None, None, None
                tot_qty = Decimal("0")
                count = 0

            result.append(
                {
                    "category_id": str(cat.id),
                    "code": cat.code,
                    "name": cat.name,
                    "unit": cat.unit,
                    "min_price_per_kg": min_p,
                    "avg_price_per_kg": avg_p,
                    "max_price_per_kg": max_p,
                    "listing_count": count,
                    "total_quantity_kg": tot_qty,
                }
            )
        return result

    @staticmethod
    def get_impact_stats(db: Session) -> dict[str, Any]:
        """Total kg counted ONLY from orders that reached delivered or completed."""
        eligible_orders = db.scalars(
            select(Order).where(Order.status.in_(["delivered", "completed"]))
        ).all()

        total_kg = Decimal("0.000")
        category_breakdown: dict[str, dict[str, Any]] = {}
        order_count = len(eligible_orders)

        for ord_item in eligible_orders:
            # Prefer delivery stage weight, then collection, then offer quantity
            kg: Decimal | None = None
            for w in ord_item.weight_records:
                if w.stage == "delivery":
                    kg = w.weight_kg
                    break
            if kg is None:
                for w in ord_item.weight_records:
                    if w.stage == "collection":
                        kg = w.weight_kg
                        break
            if kg is None:
                kg = ord_item.offer.quantity_kg

            total_kg += kg

            cat = ord_item.offer.listing.category
            cat_code = cat.code
            if cat_code not in category_breakdown:
                category_breakdown[cat_code] = {
                    "name": cat.name,
                    "total_kg": Decimal("0.000"),
                    "order_count": 0,
                }
            category_breakdown[cat_code]["total_kg"] += kg
            category_breakdown[cat_code]["order_count"] += 1

        # Estimated CO2 avoided: ~1.5 kg CO2 per kg recycled waste
        co2_saved_kg = round(total_kg * Decimal("1.5"), 2)

        return {
            "total_diverted_kg": total_kg,
            "orders_diverted_count": order_count,
            "estimated_co2_saved_kg": co2_saved_kg,
            "categories": [
                {
                    "code": code,
                    "name": data["name"],
                    "total_kg": data["total_kg"],
                    "order_count": data["order_count"],
                }
                for code, data in category_breakdown.items()
            ],
        }
