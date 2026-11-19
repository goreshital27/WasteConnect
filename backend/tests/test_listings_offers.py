
from app.modules.catalog.models import WasteCategory
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _create_category(db: Session, code: str = "paper", name: str = "Paper") -> WasteCategory:
    cat = WasteCategory(code=code, name=name, unit="kg", is_active=True)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def _register_user(client: TestClient, email: str, role: str = "individual") -> str:
    res = client.post(
        "/auth/register",
        json={
            "name": f"User {email}",
            "email": email,
            "phone": "9820011223",
            "password": "Password123!",
            "role": role,
            "area": "Wakad",
            "pincode": "411057",
        },
    )
    return res.json()["data"]["access_token"]


def test_categories_endpoint(client: TestClient, db_session: Session) -> None:
    _create_category(db_session, "pet_test", "PET Plastics")
    res = client.get("/categories")
    assert res.status_code == 200
    cats = res.json()["data"]
    assert any(c["code"] == "pet_test" for c in cats)


def test_create_and_filter_listings(client: TestClient, db_session: Session) -> None:
    cat = _create_category(db_session, "cardboard_test", "Cardboard")
    token_seller = _register_user(client, "seller1@test.com", "individual")

    payload = {
        "category_id": str(cat.id),
        "title": "Clean Moving Boxes",
        "quantity_kg": "50.000",
        "price_per_kg": "12.50",
        "is_negotiable": True,
        "area": "Wakad",
        "pincode": "411057",
    }
    create_res = client.post(
        "/listings",
        json=payload,
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    assert create_res.status_code == 201
    listing = create_res.json()["data"]
    assert listing["title"] == "Clean Moving Boxes"
    assert listing["status"] == "open"

    # Filter by category
    filter_res = client.get("/listings", params={"category": "cardboard_test"})
    assert filter_res.status_code == 200
    assert len(filter_res.json()["data"]) >= 1

    # Filter by pincode
    pin_res = client.get("/listings", params={"pincode": "411057"})
    assert pin_res.status_code == 200
    assert len(pin_res.json()["data"]) >= 1

    # Filter by min_quantity
    qty_res = client.get("/listings", params={"min_quantity": 40.0})
    assert qty_res.status_code == 200
    assert len(qty_res.json()["data"]) >= 1

    qty_none = client.get("/listings", params={"min_quantity": 100.0})
    assert qty_none.status_code == 200
    assert len(qty_none.json()["data"]) == 0


def test_self_offer_not_allowed(client: TestClient, db_session: Session) -> None:
    cat = _create_category(db_session, "iron_test", "Iron")
    token_seller = _register_user(client, "seller2@test.com", "individual")

    create_res = client.post(
        "/listings",
        json={
            "category_id": str(cat.id),
            "title": "Iron Rods",
            "quantity_kg": "25.000",
            "price_per_kg": "30.00",
            "is_negotiable": False,
            "area": "Baner",
            "pincode": "411045",
        },
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    listing_id = create_res.json()["data"]["id"]

    # Try making offer on own listing
    offer_res = client.post(
        f"/listings/{listing_id}/offers",
        json={"quantity_kg": "25.000", "price_per_kg": "28.00"},
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    assert offer_res.status_code == 400
    assert offer_res.json()["code"] == "SELF_OFFER_NOT_ALLOWED"


def test_accept_offer_permissions_and_state(client: TestClient, db_session: Session) -> None:
    cat = _create_category(db_session, "copper_test", "Copper")
    token_seller = _register_user(client, "seller3@test.com", "individual")
    token_buyer1 = _register_user(client, "buyer1@test.com", "reseller")
    token_buyer2 = _register_user(client, "buyer2@test.com", "reseller")
    token_stranger = _register_user(client, "stranger@test.com", "individual")

    # Seller creates listing
    create_res = client.post(
        "/listings",
        json={
            "category_id": str(cat.id),
            "title": "Copper Cable",
            "quantity_kg": "10.000",
            "price_per_kg": "450.00",
            "is_negotiable": True,
            "area": "Hinjawadi",
            "pincode": "411057",
        },
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    listing_id = create_res.json()["data"]["id"]

    # Buyer 1 makes offer
    offer1_res = client.post(
        f"/listings/{listing_id}/offers",
        json={"quantity_kg": "10.000", "price_per_kg": "440.00"},
        headers={"Authorization": f"Bearer {token_buyer1}"},
    )
    assert offer1_res.status_code == 201
    offer1_id = offer1_res.json()["data"]["id"]

    # Buyer 2 makes offer
    offer2_res = client.post(
        f"/listings/{listing_id}/offers",
        json={"quantity_kg": "10.000", "price_per_kg": "430.00"},
        headers={"Authorization": f"Bearer {token_buyer2}"},
    )
    assert offer2_res.status_code == 201
    offer2_id = offer2_res.json()["data"]["id"]

    # Stranger tries to accept Buyer 1's offer -> FORBIDDEN
    stranger_accept = client.post(
        f"/offers/{offer1_id}/accept",
        headers={"Authorization": f"Bearer {token_stranger}"},
    )
    assert stranger_accept.status_code == 403
    assert stranger_accept.json()["code"] == "FORBIDDEN"

    # Seller accepts Buyer 1's offer
    seller_accept = client.post(
        f"/offers/{offer1_id}/accept",
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    assert seller_accept.status_code == 200
    accept_data = seller_accept.json()["data"]
    assert accept_data["offer"]["status"] == "accepted"
    assert "order_id" in accept_data

    # Verify listing is now sold
    listing_check = client.get(f"/listings/{listing_id}")
    assert listing_check.json()["data"]["status"] == "sold"

    # Verify Buyer 2's offer was automatically rejected
    buyer2_sent = client.get("/offers/sent", headers={"Authorization": f"Bearer {token_buyer2}"})
    assert buyer2_sent.status_code == 200
    b2_offers = buyer2_sent.json()["data"]
    b2_matching = next(o for o in b2_offers if o["id"] == offer2_id)
    assert b2_matching["status"] == "rejected"
