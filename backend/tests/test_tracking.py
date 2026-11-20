from decimal import Decimal
from uuid import UUID

from app.core.security import create_access_token, hash_password
from app.modules.auth.models import User
from app.modules.catalog.models import WasteCategory
from app.modules.listings.models import Listing
from app.modules.offers.models import Offer
from app.modules.orders.models import Order
from app.modules.tracking.models import TrackingPosition
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _setup_order(client: TestClient, db: Session) -> tuple[str, str, str, str]:
    """Helper creating a category, seller, buyer, listing, offer, and confirmed order."""
    cat = WasteCategory(code="track_alu", name="Aluminium Tracking", unit="kg", is_active=True)
    db.add(cat)

    seller = User(
        name="Tracking Seller",
        email="tseller@example.com",
        phone="9820088111",
        password_hash=hash_password("Password123!"),
        role="individual",
        area="Baner",
        pincode="411045",
    )
    buyer = User(
        name="Tracking Buyer",
        email="tbuyer@example.com",
        phone="9820088222",
        password_hash=hash_password("Password123!"),
        role="reseller",
        area="Wakad",
        pincode="411057",
    )
    db.add(seller)
    db.add(buyer)
    db.flush()

    listing = Listing(
        seller_id=seller.id,
        category_id=cat.id,
        title="Clean Aluminium Offcuts",
        quantity_kg=Decimal("25.000"),
        price_per_kg=Decimal("130.00"),
        is_negotiable=False,
        area="Baner",
        pincode="411045",
        status="open",
    )
    db.add(listing)
    db.flush()

    offer = Offer(
        listing_id=listing.id,
        buyer_id=buyer.id,
        quantity_kg=Decimal("25.000"),
        price_per_kg=Decimal("130.00"),
        status="accepted",
    )
    db.add(offer)
    db.flush()

    order = Order(
        offer_id=offer.id,
        seller_id=seller.id,
        buyer_id=buyer.id,
        status="confirmed",
    )
    db.add(order)
    db.commit()

    token_seller = create_access_token({"sub": str(seller.id)})
    token_buyer = create_access_token({"sub": str(buyer.id)})

    return token_seller, token_buyer, str(listing.id), str(order.id)


def test_buyer_can_post_and_seller_can_read(client: TestClient, db_session: Session) -> None:
    token_seller, token_buyer, _, order_id = _setup_order(client, db_session)

    # Record collection weight then transition order to 'collected'
    w_res = client.post(
        f"/orders/{order_id}/weights",
        json={"stage": "collection", "weight_kg": "25.000"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    assert w_res.status_code == 201

    trans_res = client.post(
        f"/orders/{order_id}/transition",
        json={"target_status": "collected"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    assert trans_res.status_code == 200

    # 1. Buyer posts position
    post_res = client.post(
        f"/tracking/orders/{order_id}/position",
        json={"lat": "18.598500", "lng": "73.763500"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    assert post_res.status_code == 200
    post_data = post_res.json()
    assert post_data["code"] == "SUCCESS"
    assert Decimal(str(post_data["data"]["lat"])) == Decimal("18.598500")
    assert Decimal(str(post_data["data"]["lng"])) == Decimal("73.763500")
    assert post_data["data"]["order_id"] == order_id

    # 2. Seller reads position
    get_res = client.get(
        f"/tracking/orders/{order_id}/position",
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["code"] == "SUCCESS"
    assert Decimal(str(get_data["data"]["lat"])) == Decimal("18.598500")
    assert Decimal(str(get_data["data"]["lng"])) == Decimal("73.763500")
    assert get_data["data"]["order_id"] == order_id

    # 3. Buyer posts updated position (upsert check - latest point only)
    post_res2 = client.post(
        f"/tracking/orders/{order_id}/position",
        json={"lat": "18.550500", "lng": "73.790000"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    assert post_res2.status_code == 200
    assert Decimal(str(post_res2.json()["data"]["lat"])) == Decimal("18.550500")

    get_res2 = client.get(
        f"/tracking/orders/{order_id}/position",
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    assert get_res2.status_code == 200
    assert Decimal(str(get_res2.json()["data"]["lat"])) == Decimal("18.550500")

    # Verify database table has only 1 row for this order
    positions = db_session.query(TrackingPosition).filter_by(order_id=UUID(order_id)).all()
    assert len(positions) == 1
    assert Decimal(str(positions[0].lat)) == Decimal("18.550500")


def test_stranger_gets_403(client: TestClient, db_session: Session) -> None:
    token_seller, token_buyer, _, order_id = _setup_order(client, db_session)

    # Transition to collected
    client.post(
        f"/orders/{order_id}/weights",
        json={"stage": "collection", "weight_kg": "25.000"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    client.post(
        f"/orders/{order_id}/transition",
        json={"target_status": "collected"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )

    # Register stranger
    stranger = User(
        name="Stranger User",
        email="stranger@example.com",
        phone="9820099999",
        password_hash=hash_password("Password123!"),
        role="individual",
        area="Kothrud",
        pincode="411038",
    )
    db_session.add(stranger)
    db_session.commit()
    token_stranger = create_access_token({"sub": str(stranger.id)})

    # Stranger POST -> 403
    s_post = client.post(
        f"/tracking/orders/{order_id}/position",
        json={"lat": "18.598500", "lng": "73.763500"},
        headers={"Authorization": f"Bearer {token_stranger}"},
    )
    assert s_post.status_code == 403
    assert s_post.json()["code"] == "FORBIDDEN"

    # Stranger GET -> 403
    s_get = client.get(
        f"/tracking/orders/{order_id}/position",
        headers={"Authorization": f"Bearer {token_stranger}"},
    )
    assert s_get.status_code == 403
    assert s_get.json()["code"] == "FORBIDDEN"

    # Seller POST (seller is not buyer) -> 403
    seller_post = client.post(
        f"/tracking/orders/{order_id}/position",
        json={"lat": "18.598500", "lng": "73.763500"},
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    assert seller_post.status_code == 403
    assert seller_post.json()["code"] == "FORBIDDEN"


def test_posting_rejected_when_order_not_collected(
    client: TestClient,
    db_session: Session,
) -> None:
    token_seller, token_buyer, _, order_id = _setup_order(client, db_session)

    # Order is currently 'confirmed' (not collected)
    post_res = client.post(
        f"/tracking/orders/{order_id}/position",
        json={"lat": "18.598500", "lng": "73.763500"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    assert post_res.status_code == 400
    assert post_res.json()["code"] == "INVALID_ORDER_STATUS"

    get_res = client.get(
        f"/tracking/orders/{order_id}/position",
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    assert get_res.status_code == 400
    assert get_res.json()["code"] == "INVALID_ORDER_STATUS"

    # Transition order to collected, then delivered
    client.post(
        f"/orders/{order_id}/weights",
        json={"stage": "collection", "weight_kg": "25.000"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    client.post(
        f"/orders/{order_id}/transition",
        json={"target_status": "collected"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    client.post(
        f"/orders/{order_id}/weights",
        json={"stage": "delivery", "weight_kg": "24.800"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    client.post(
        f"/orders/{order_id}/transition",
        json={"target_status": "delivered"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )

    # Now in 'delivered' status -> posting rejected
    post_res2 = client.post(
        f"/tracking/orders/{order_id}/position",
        json={"lat": "18.598500", "lng": "73.763500"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    assert post_res2.status_code == 400
    assert post_res2.json()["code"] == "INVALID_ORDER_STATUS"

    # Reading also rejected when delivered
    get_res2 = client.get(
        f"/tracking/orders/{order_id}/position",
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    assert get_res2.status_code == 400
    assert get_res2.json()["code"] == "INVALID_ORDER_STATUS"
