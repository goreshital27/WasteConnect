import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import get_session_factory  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.modules.auth.models import User  # noqa: E402
from app.modules.catalog.models import WasteCategory  # noqa: E402
from app.modules.listings.models import Listing  # noqa: E402
from app.modules.matching.service import MatchingService  # noqa: E402
from app.modules.notifications.models import Notification  # noqa: E402
from app.modules.offers.models import Offer  # noqa: E402
from app.modules.orders.models import (  # noqa: E402
    Order,
    OrderStatusHistory,
    WeightRecord,
)
from app.modules.requirements.models import Requirement  # noqa: E402
from sqlalchemy import delete  # noqa: E402

DEMO_PASSWORD = "Password123!"


def seed() -> None:
    print("Pre-computing password hash...")
    pw_hash = hash_password(DEMO_PASSWORD)

    session_factory = get_session_factory()
    db = session_factory()
    try:
        print("Cleaning previous demo data...")
        db.execute(delete(Notification))
        db.execute(delete(Requirement))
        db.execute(delete(WeightRecord))
        db.execute(delete(OrderStatusHistory))
        db.execute(delete(Order))
        db.execute(delete(Offer))
        db.execute(delete(Listing))
        db.execute(delete(WasteCategory))
        db.execute(delete(User))
        db.commit()

        print("Seeding waste categories (dry + wet)...")
        categories_data = [
            # Dry categories
            ("paper", "Office Paper & Books", "kg", "dry", False, None),
            ("newspaper", "Old Newspaper (Raddi)", "kg", "dry", False, None),
            ("cardboard", "Corrugated Cardboard / Cartons", "kg", "dry", False, None),
            ("pet", "PET Bottles & Poly Containers", "kg", "dry", False, None),
            ("hdpe", "HDPE Rigid Plastics & Cans", "kg", "dry", False, None),
            ("iron", "Scrap Iron & Castings", "kg", "dry", False, None),
            ("steel", "Stainless Steel (SS) Scrap", "kg", "dry", False, None),
            ("aluminium", "Aluminium Scrap & Utensils", "kg", "dry", False, None),
            ("copper", "Copper Wire & Scrap", "kg", "dry", False, None),
            ("glass", "Glass Bottles & Cullet", "kg", "dry", False, None),
            # Wet categories (allows zero/negative price, has expiry)
            ("food_waste", "Commercial & Kitchen Food Waste", "kg", "wet", True, 24),
            ("garden_waste", "Garden Waste & Organic Greens", "kg", "wet", True, 48),
        ]
        cat_map: dict[str, WasteCategory] = {}
        for code, name, unit, stream, zero_neg, exp_h in categories_data:
            cat = WasteCategory(
                code=code,
                name=name,
                unit=unit,
                stream=stream,
                allows_zero_or_negative_price=zero_neg,
                expiry_hours=exp_h,
                is_active=True,
            )
            db.add(cat)
            cat_map[code] = cat
        db.flush()

        print("Seeding demo users across Pune (Households, Resellers, Processors, Businesses)...")
        users_data = [
            # Households (Individual)
            (
                "Aarav Sharma",
                "aarav.sharma@example.com",
                "9820011001",
                "individual",
                "Wakad",
                "411057",
            ),
            (
                "Priya Patil",
                "priya.patil@example.com",
                "9820011002",
                "individual",
                "Baner",
                "411045",
            ),
            (
                "Rohit Deshmukh",
                "rohit.d@example.com",
                "9820011003",
                "individual",
                "Hinjawadi",
                "411057",
            ),
            (
                "Ananya Kulkarni",
                "ananya.k@example.com",
                "9820011004",
                "individual",
                "Kharadi",
                "411014",
            ),
            (
                "Vikram Joshi",
                "vikram.j@example.com",
                "9820011005",
                "individual",
                "Hadapsar",
                "411028",
            ),
            # Resellers (Scrap dealers)
            (
                "Sunil Scrap Traders",
                "sunil.scrap@example.com",
                "9820022001",
                "reseller",
                "Wakad",
                "411057",
            ),
            (
                "Maharashtra Eco",
                "maha.eco@example.com",
                "9820022002",
                "reseller",
                "Baner",
                "411045",
            ),
            (
                "Pimpri Scrap Mart",
                "pimpri.scrap@example.com",
                "9820022003",
                "reseller",
                "Pimpri",
                "411018",
            ),
            # Aggregator & Recycler
            (
                "Pune Aggregators",
                "pune.agg@example.com",
                "9820033001",
                "aggregator",
                "Hadapsar",
                "411028",
            ),
            (
                "Sahyadri Recyclers",
                "sahyadri.rec@example.com",
                "9820044001",
                "recycler",
                "Pimpri",
                "411018",
            ),
            # Processors (Wet waste buyers)
            (
                "Pune Biogas Energy",
                "pune.biogas@example.com",
                "9820055001",
                "processor",
                "Hadapsar",
                "411028",
            ),
            (
                "EcoCompost Pune Ltd",
                "ecocompost.pune@example.com",
                "9820055002",
                "processor",
                "Baner",
                "411045",
            ),
            # Businesses (Hotels, restaurants, societies; can sell wet/dry waste)
            (
                "Hotel Marigold Baner",
                "marigold.hotel@example.com",
                "9820066001",
                "business",
                "Baner",
                "411045",
            ),
            (
                "Amanora Town Society",
                "amanora.society@example.com",
                "9820066002",
                "business",
                "Hadapsar",
                "411028",
            ),
        ]

        user_map: dict[str, User] = {}
        for name, email, phone, role, area, pincode in users_data:
            user = User(
                name=name,
                email=email,
                phone=phone,
                password_hash=pw_hash,
                role=role,
                area=area,
                pincode=pincode,
            )
            db.add(user)
            user_map[email] = user
        db.flush()

        now = datetime.now(UTC)
        print("Seeding ~29 listings (dry scrap + wet waste with expiry)...")
        listings_spec = [
            # Dry listings
            (
                "aarav.sharma@example.com",
                "newspaper",
                "Monthly Raddi Newspaper Stack",
                "28.5",
                "14.5",
                True,
                "Wakad",
                "411057",
                "open",
                None,
            ),
            (
                "aarav.sharma@example.com",
                "cardboard",
                "Amazon Delivery Packing Boxes",
                "35.0",
                "12.0",
                True,
                "Wakad",
                "411057",
                "open",
                None,
            ),
            (
                "aarav.sharma@example.com",
                "iron",
                "Old Balcony Grills & Bed Frame",
                "65.0",
                "31.0",
                False,
                "Wakad",
                "411057",
                "sold",
                None,
            ),
            (
                "priya.patil@example.com",
                "paper",
                "Old College Textbooks & Notebooks",
                "45.0",
                "13.0",
                True,
                "Baner",
                "411045",
                "open",
                None,
            ),
            (
                "priya.patil@example.com",
                "pet",
                "Sorted Mineral Water Bottles",
                "22.5",
                "24.0",
                True,
                "Baner",
                "411045",
                "open",
                None,
            ),
            (
                "priya.patil@example.com",
                "glass",
                "Beer & Wine Glass Bottles",
                "50.0",
                "3.5",
                False,
                "Baner",
                "411045",
                "sold",
                None,
            ),
            (
                "rohit.d@example.com",
                "newspaper",
                "Society Collected Newspapers",
                "80.0",
                "15.0",
                True,
                "Hinjawadi",
                "411057",
                "open",
                None,
            ),
            (
                "rohit.d@example.com",
                "cardboard",
                "IT Office Relocation Cartons",
                "120.0",
                "12.5",
                True,
                "Hinjawadi",
                "411057",
                "open",
                None,
            ),
            (
                "rohit.d@example.com",
                "copper",
                "Air Conditioner Copper Piping",
                "14.0",
                "460.0",
                False,
                "Hinjawadi",
                "411057",
                "sold",
                None,
            ),
            (
                "ananya.k@example.com",
                "pet",
                "Clean Crushed PET Plastic",
                "38.0",
                "23.5",
                True,
                "Kharadi",
                "411014",
                "open",
                None,
            ),
            (
                "ananya.k@example.com",
                "hdpe",
                "Household Detergent Bottles Lot",
                "42.0",
                "29.0",
                True,
                "Kharadi",
                "411014",
                "open",
                None,
            ),
            (
                "ananya.k@example.com",
                "aluminium",
                "Soda Cans & Broken Cookware",
                "18.5",
                "115.0",
                False,
                "Kharadi",
                "411014",
                "sold",
                None,
            ),
            (
                "vikram.j@example.com",
                "steel",
                "Kitchen Utensils & Rods",
                "40.0",
                "68.0",
                True,
                "Hadapsar",
                "411028",
                "open",
                None,
            ),
            (
                "vikram.j@example.com",
                "iron",
                "Dismantled Gym Weights & Bars",
                "110.0",
                "33.0",
                True,
                "Hadapsar",
                "411028",
                "open",
                None,
            ),
            (
                "vikram.j@example.com",
                "newspaper",
                "Old Gazette & Magazines Bundle",
                "32.0",
                "14.0",
                True,
                "Hadapsar",
                "411028",
                "cancelled",
                None,
            ),
            (
                "sunil.scrap@example.com",
                "cardboard",
                "Baled Corrugated Boxes Lot",
                "450.0",
                "13.2",
                False,
                "Wakad",
                "411057",
                "open",
                None,
            ),
            (
                "sunil.scrap@example.com",
                "pet",
                "Sorted White PET Flakes",
                "250.0",
                "25.0",
                True,
                "Wakad",
                "411057",
                "open",
                None,
            ),
            (
                "sunil.scrap@example.com",
                "hdpe",
                "Industrial Drum Scrap",
                "300.0",
                "31.5",
                True,
                "Wakad",
                "411057",
                "sold",
                None,
            ),
            (
                "maha.eco@example.com",
                "iron",
                "Heavy Cast Iron Machinery Scrap",
                "600.0",
                "34.0",
                False,
                "Baner",
                "411045",
                "open",
                None,
            ),
            (
                "maha.eco@example.com",
                "copper",
                "Stripped Heavy Copper Cable",
                "85.0",
                "480.0",
                True,
                "Baner",
                "411045",
                "open",
                None,
            ),
            (
                "maha.eco@example.com",
                "aluminium",
                "Aluminium Window Sections Scrap",
                "160.0",
                "122.0",
                True,
                "Baner",
                "411045",
                "open",
                None,
            ),
            (
                "pimpri.scrap@example.com",
                "steel",
                "SS 304 Fabrication Offcuts",
                "220.0",
                "72.0",
                True,
                "Pimpri",
                "411018",
                "open",
                None,
            ),
            (
                "pimpri.scrap@example.com",
                "paper",
                "Shredded Bank Document Paper",
                "350.0",
                "13.8",
                False,
                "Pimpri",
                "411018",
                "open",
                None,
            ),
            (
                "pimpri.scrap@example.com",
                "glass",
                "Mixed Clear Bottle Cullet",
                "400.0",
                "4.0",
                True,
                "Pimpri",
                "411018",
                "open",
                None,
            ),
            (
                "pimpri.scrap@example.com",
                "iron",
                "Light Iron Scrap Mix",
                "180.0",
                "29.5",
                True,
                "Pimpri",
                "411018",
                "open",
                None,
            ),
            # 4 Wet listings
            (
                "marigold.hotel@example.com",
                "food_waste",
                "Hotel Kitchen Fresh Buffet & Preparation Scrap",
                "220.0",
                "0.00",
                False,
                "Baner",
                "411045",
                "open",
                now + timedelta(hours=20),
            ),
            (
                "marigold.hotel@example.com",
                "food_waste",
                "Bulk Food Waste Lot (Processor Disposal Fee Paid)",
                "350.0",
                "-1.50",
                True,
                "Baner",
                "411045",
                "open",
                now + timedelta(hours=18),
            ),
            (
                "amanora.society@example.com",
                "garden_waste",
                "Township Lawnmower Greens & Tree Trimmings",
                "450.0",
                "0.00",
                False,
                "Hadapsar",
                "411028",
                "open",
                now + timedelta(hours=44),
            ),
            (
                "amanora.society@example.com",
                "food_waste",
                "Residential Society Segregated Kitchen Compostable Waste",
                "180.0",
                "1.00",
                True,
                "Hadapsar",
                "411028",
                "open",
                now + timedelta(hours=22),
            ),
            # 1 Expired listing for testing expired rules
            (
                "marigold.hotel@example.com",
                "food_waste",
                "Expired Wet Waste Lot (Past Expiry Window)",
                "90.0",
                "0.00",
                False,
                "Baner",
                "411045",
                "open",
                now - timedelta(hours=5),
            ),
        ]

        created_listings: list[Listing] = []
        for (
            s_email,
            c_code,
            title,
            qty,
            price,
            neg,
            area,
            pin,
            status_str,
            exp_time,
        ) in listings_spec:
            seller = user_map[s_email]
            cat = cat_map[c_code]
            listing = Listing(
                seller_id=seller.id,
                category_id=cat.id,
                title=title,
                quantity_kg=Decimal(qty),
                price_per_kg=Decimal(price),
                is_negotiable=neg,
                area=area,
                pincode=pin,
                status=status_str,
                expires_at=exp_time,
            )
            db.add(listing)
            created_listings.append(listing)
        db.flush()

        print("Seeding demo orders...")
        # Order 1: Confirmed
        iron_listing = created_listings[2]
        offer1 = Offer(
            listing_id=iron_listing.id,
            buyer_id=user_map["sunil.scrap@example.com"].id,
            quantity_kg=Decimal("65.000"),
            price_per_kg=Decimal("30.50"),
            status="accepted",
        )
        offer1_rejected = Offer(
            listing_id=iron_listing.id,
            buyer_id=user_map["maha.eco@example.com"].id,
            quantity_kg=Decimal("65.000"),
            price_per_kg=Decimal("28.00"),
            status="rejected",
        )
        db.add(offer1)
        db.add(offer1_rejected)
        db.flush()

        order1 = Order(
            offer_id=offer1.id,
            seller_id=iron_listing.seller_id,
            buyer_id=offer1.buyer_id,
            status="confirmed",
        )
        db.add(order1)
        db.flush()
        db.add(
            OrderStatusHistory(
                order_id=order1.id,
                from_status=None,
                to_status="confirmed",
                changed_by_id=iron_listing.seller_id,
            )
        )

        # Order 2: Collected
        glass_listing = created_listings[5]
        offer2 = Offer(
            listing_id=glass_listing.id,
            buyer_id=user_map["maha.eco@example.com"].id,
            quantity_kg=Decimal("50.000"),
            price_per_kg=Decimal("3.50"),
            status="accepted",
        )
        db.add(offer2)
        db.flush()

        order2 = Order(
            offer_id=offer2.id,
            seller_id=glass_listing.seller_id,
            buyer_id=offer2.buyer_id,
            status="collected",
        )
        db.add(order2)
        db.flush()
        db.add(
            OrderStatusHistory(
                order_id=order2.id,
                from_status=None,
                to_status="confirmed",
                changed_by_id=glass_listing.seller_id,
            )
        )
        db.add(
            OrderStatusHistory(
                order_id=order2.id,
                from_status="confirmed",
                to_status="collected",
                changed_by_id=offer2.buyer_id,
            )
        )
        db.add(WeightRecord(order_id=order2.id, stage="collection", weight_kg=Decimal("51.200")))

        # Order 3: Delivered
        copper_listing = created_listings[8]
        offer3 = Offer(
            listing_id=copper_listing.id,
            buyer_id=user_map["pimpri.scrap@example.com"].id,
            quantity_kg=Decimal("14.000"),
            price_per_kg=Decimal("460.00"),
            status="accepted",
        )
        db.add(offer3)
        db.flush()

        order3 = Order(
            offer_id=offer3.id,
            seller_id=copper_listing.seller_id,
            buyer_id=offer3.buyer_id,
            status="delivered",
        )
        db.add(order3)
        db.flush()
        db.add(
            OrderStatusHistory(
                order_id=order3.id,
                from_status=None,
                to_status="confirmed",
                changed_by_id=copper_listing.seller_id,
            )
        )
        db.add(
            OrderStatusHistory(
                order_id=order3.id,
                from_status="confirmed",
                to_status="collected",
                changed_by_id=offer3.buyer_id,
            )
        )
        db.add(
            OrderStatusHistory(
                order_id=order3.id,
                from_status="collected",
                to_status="delivered",
                changed_by_id=offer3.buyer_id,
            )
        )
        db.add(WeightRecord(order_id=order3.id, stage="collection", weight_kg=Decimal("14.300")))
        db.add(WeightRecord(order_id=order3.id, stage="delivery", weight_kg=Decimal("13.950")))

        # Order 4: Completed
        alu_listing = created_listings[11]
        offer4 = Offer(
            listing_id=alu_listing.id,
            buyer_id=user_map["sahyadri.rec@example.com"].id,
            quantity_kg=Decimal("18.500"),
            price_per_kg=Decimal("115.00"),
            status="accepted",
        )
        db.add(offer4)
        db.flush()

        order4 = Order(
            offer_id=offer4.id,
            seller_id=alu_listing.seller_id,
            buyer_id=offer4.buyer_id,
            status="completed",
        )
        db.add(order4)
        db.flush()
        db.add(
            OrderStatusHistory(
                order_id=order4.id,
                from_status=None,
                to_status="confirmed",
                changed_by_id=alu_listing.seller_id,
            )
        )
        db.add(
            OrderStatusHistory(
                order_id=order4.id,
                from_status="confirmed",
                to_status="collected",
                changed_by_id=offer4.buyer_id,
            )
        )
        db.add(
            OrderStatusHistory(
                order_id=order4.id,
                from_status="collected",
                to_status="delivered",
                changed_by_id=offer4.buyer_id,
            )
        )
        db.add(
            OrderStatusHistory(
                order_id=order4.id,
                from_status="delivered",
                to_status="completed",
                changed_by_id=offer4.buyer_id,
            )
        )
        db.add(WeightRecord(order_id=order4.id, stage="collection", weight_kg=Decimal("18.800")))
        db.add(WeightRecord(order_id=order4.id, stage="delivery", weight_kg=Decimal("18.400")))

        # Order 5: Completed
        hdpe_listing = created_listings[17]
        offer5 = Offer(
            listing_id=hdpe_listing.id,
            buyer_id=user_map["pune.agg@example.com"].id,
            quantity_kg=Decimal("300.000"),
            price_per_kg=Decimal("31.00"),
            status="accepted",
        )
        db.add(offer5)
        db.flush()

        order5 = Order(
            offer_id=offer5.id,
            seller_id=hdpe_listing.seller_id,
            buyer_id=offer5.buyer_id,
            status="completed",
        )
        db.add(order5)
        db.flush()
        db.add(
            OrderStatusHistory(
                order_id=order5.id,
                from_status=None,
                to_status="confirmed",
                changed_by_id=hdpe_listing.seller_id,
            )
        )
        db.add(
            OrderStatusHistory(
                order_id=order5.id,
                from_status="confirmed",
                to_status="collected",
                changed_by_id=offer5.buyer_id,
            )
        )
        db.add(
            OrderStatusHistory(
                order_id=order5.id,
                from_status="collected",
                to_status="delivered",
                changed_by_id=offer5.buyer_id,
            )
        )
        db.add(
            OrderStatusHistory(
                order_id=order5.id,
                from_status="delivered",
                to_status="completed",
                changed_by_id=offer5.buyer_id,
            )
        )
        db.add(WeightRecord(order_id=order5.id, stage="collection", weight_kg=Decimal("302.000")))
        db.add(WeightRecord(order_id=order5.id, stage="delivery", weight_kg=Decimal("298.500")))

        # Pending offers
        db.add(
            Offer(
                listing_id=created_listings[0].id,
                buyer_id=user_map["sunil.scrap@example.com"].id,
                quantity_kg=Decimal("28.500"),
                price_per_kg=Decimal("14.00"),
                status="pending",
            )
        )
        db.add(
            Offer(
                listing_id=created_listings[1].id,
                buyer_id=user_map["pimpri.scrap@example.com"].id,
                quantity_kg=Decimal("35.000"),
                price_per_kg=Decimal("11.50"),
                status="pending",
            )
        )
        db.flush()

        print("Seeding 5 requirements and generating match notifications...")
        requirements_data = [
            # 1. Sunil Scrap (reseller) wants Cardboard in Wakad (411057)
            ("sunil.scrap@example.com", "cardboard", "100.000", "13.00", "411057"),
            # 2. Maharashtra Eco (reseller) wants Scrap Iron in Baner (411045)
            ("maha.eco@example.com", "iron", "250.000", "35.00", "411045"),
            # 3. Pimpri Scrap Mart (reseller) wants Steel in Pimpri (411018)
            ("pimpri.scrap@example.com", "steel", "150.000", "75.00", "411018"),
            # 4. Pune Biogas (processor) wants Food Waste in Hadapsar (411028)
            ("pune.biogas@example.com", "food_waste", "500.000", "1.50", "411028"),
            # 5. EcoCompost Pune (processor) wants Garden Waste in Baner (411045)
            ("ecocompost.pune@example.com", "garden_waste", "300.000", "0.50", "411045"),
        ]

        for b_email, c_code, q_kg, max_p, p_code in requirements_data:
            buyer = user_map[b_email]
            cat = cat_map[c_code]
            req_item = Requirement(
                buyer_id=buyer.id,
                category_id=cat.id,
                quantity_kg=Decimal(q_kg),
                max_price_per_kg=Decimal(max_p),
                pincode=p_code,
                status="open",
            )
            db.add(req_item)
            db.flush()
            # Generate matching notifications
            MatchingService.match_new_requirement(db, req_item)

        db.commit()
        print("\n=== Demo Seed Completed Successfully ===")
        print("NOTE: All data is demo data; prices and figures are illustrative.\n")
        print("Demo Logins (Password for all accounts: " + DEMO_PASSWORD + "):")
        print("-" * 75)
        for name, email, _phone, role, area, pincode in users_data:
            print(f"[{role.upper():11s}] {name:24s} | {email:28s} | {area} ({pincode})")
        print("-" * 75)

    finally:
        db.close()


if __name__ == "__main__":
    seed()
