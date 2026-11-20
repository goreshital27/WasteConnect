import uuid
from datetime import UTC, datetime, timedelta

from app.modules.catalog.models import WasteCategory
from app.modules.listings.models import Listing
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _register(client: TestClient, email: str, role: str, pincode: str = "411057") -> str:
    res = client.post(
        "/auth/register",
        json={
            "name": f"User {email}",
            "email": email,
            "phone": "9820011999",
            "password": "Password123!",
            "role": role,
            "area": "Pune Local",
            "pincode": pincode,
        },
    )
    return res.json()["data"]["access_token"]


def test_price_rule_dry_vs_wet(client: TestClient, db_session: Session) -> None:
    # 1. Dry category (positive price required)
    dry_cat = WasteCategory(
        code="dry_test_cat",
        name="Dry Scrap Test",
        unit="kg",
        stream="dry",
        allows_zero_or_negative_price=False,
        is_active=True,
    )
    # 2. Wet category (zero/negative price allowed)
    wet_cat = WasteCategory(
        code="wet_test_cat",
        name="Wet Scrap Test",
        unit="kg",
        stream="wet",
        allows_zero_or_negative_price=True,
        expiry_hours=24,
        is_active=True,
    )
    db_session.add_all([dry_cat, wet_cat])
    db_session.commit()

    token_seller = _register(client, "seller_price@test.com", "individual")

    # Dry category with zero price must fail
    res_zero = client.post(
        "/listings",
        json={
            "category_id": str(dry_cat.id),
            "title": "Dry Zero Price Test",
            "quantity_kg": "50.0",
            "price_per_kg": "0.0",
            "area": "Wakad",
            "pincode": "411057",
        },
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    assert res_zero.status_code == 400
    assert res_zero.json()["code"] == "PRICE_MUST_BE_POSITIVE"

    # Dry category with negative price must fail
    res_neg = client.post(
        "/listings",
        json={
            "category_id": str(dry_cat.id),
            "title": "Dry Neg Price Test",
            "quantity_kg": "50.0",
            "price_per_kg": "-5.0",
            "area": "Wakad",
            "pincode": "411057",
        },
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    assert res_neg.status_code == 400

    # Wet category with zero price must succeed
    res_wet_zero = client.post(
        "/listings",
        json={
            "category_id": str(wet_cat.id),
            "title": "Wet Free Scrap Test",
            "quantity_kg": "100.0",
            "price_per_kg": "0.0",
            "area": "Wakad",
            "pincode": "411057",
        },
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    assert res_wet_zero.status_code == 201
    assert float(res_wet_zero.json()["data"]["price_per_kg"]) == 0.0

    # Wet category with negative price (tipping/processing fee) must succeed
    res_wet_neg = client.post(
        "/listings",
        json={
            "category_id": str(wet_cat.id),
            "title": "Wet Disposal Fee Test",
            "quantity_kg": "200.0",
            "price_per_kg": "-1.50",
            "area": "Wakad",
            "pincode": "411057",
        },
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    assert res_wet_neg.status_code == 201
    assert float(res_wet_neg.json()["data"]["price_per_kg"]) == -1.50


def test_expired_listing_rejects_offers(client: TestClient, db_session: Session) -> None:
    cat = WasteCategory(
        code="wet_expiry_test",
        name="Wet Food Test",
        unit="kg",
        stream="wet",
        allows_zero_or_negative_price=True,
        expiry_hours=12,
        is_active=True,
    )
    db_session.add(cat)
    db_session.commit()

    token_seller = _register(client, "seller_expiry@test.com", "business")
    token_buyer = _register(client, "buyer_expiry@test.com", "processor")

    # Create listing
    res_l = client.post(
        "/listings",
        json={
            "category_id": str(cat.id),
            "title": "Kitchen Waste Expired Test",
            "quantity_kg": "150.0",
            "price_per_kg": "0.0",
            "area": "Baner",
            "pincode": "411045",
        },
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    assert res_l.status_code == 201
    listing_id = res_l.json()["data"]["id"]
    listing_uuid = uuid.UUID(listing_id)

    # Manually expire the listing in database
    past_time = datetime.now(UTC) - timedelta(hours=2)
    listing = db_session.query(Listing).filter(Listing.id == listing_uuid).first()
    assert listing is not None
    listing.expires_at = past_time
    db_session.commit()

    # Buyer attempts to make an offer on expired listing
    res_offer = client.post(
        f"/listings/{listing_id}/offers",
        json={
            "quantity_kg": "150.0",
            "price_per_kg": "0.0",
        },
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    assert res_offer.status_code == 400
    assert res_offer.json()["code"] == "LISTING_EXPIRED"


def test_requirement_matching_and_notifications(
    client: TestClient, db_session: Session
) -> None:
    cat = WasteCategory(
        code="match_cat_test",
        name="Matching PET Bottles",
        unit="kg",
        stream="dry",
        allows_zero_or_negative_price=False,
        is_active=True,
    )
    db_session.add(cat)
    db_session.commit()

    token_reseller = _register(
        client, "reseller_match@test.com", "reseller", pincode="411057"
    )
    token_seller = _register(
        client, "seller_match@test.com", "individual", pincode="411057"
    )

    # 1. Reseller posts a procurement requirement for 411057
    req_res = client.post(
        "/requirements",
        json={
            "category_id": str(cat.id),
            "quantity_kg": "300.0",
            "max_price_per_kg": "25.0",
            "pincode": "411057",
        },
        headers={"Authorization": f"Bearer {token_reseller}"},
    )
    assert req_res.status_code == 201
    assert req_res.json()["data"]["status"] == "open"

    # 2. Seller posts a listing in the same pincode 411057
    list_res = client.post(
        "/listings",
        json={
            "category_id": str(cat.id),
            "title": "300kg Sorted PET Bottles Lot",
            "quantity_kg": "300.0",
            "price_per_kg": "24.0",
            "area": "Wakad",
            "pincode": "411057",
        },
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    assert list_res.status_code == 201

    # 3. Reseller should receive a match notification
    notif_res = client.get(
        "/notifications",
        headers={"Authorization": f"Bearer {token_reseller}"},
    )
    assert notif_res.status_code == 200
    data = notif_res.json()["data"]
    assert data["unread_count"] >= 1
    assert any("match" in n["message"].lower() for n in data["items"])

    notif_id = data["items"][0]["id"]

    # 4. Mark notification as read
    read_res = client.post(
        f"/notifications/{notif_id}/read",
        headers={"Authorization": f"Bearer {token_reseller}"},
    )
    assert read_res.status_code == 200
    assert read_res.json()["data"]["read_at"] is not None
