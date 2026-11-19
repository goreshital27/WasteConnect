from app.modules.catalog.models import WasteCategory
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _setup_order(client: TestClient, db: Session) -> tuple[str, str, str, str]:
    """Helper creating a category, seller, buyer, listing, offer, and confirmed order."""
    cat = WasteCategory(code="alu_test", name="Aluminium", unit="kg", is_active=True)
    db.add(cat)
    db.commit()
    db.refresh(cat)

    # Register seller & buyer
    s_res = client.post(
        "/auth/register",
        json={
            "name": "Order Seller",
            "email": "oseller@test.com",
            "phone": "9820011444",
            "password": "Password123!",
            "role": "individual",
            "area": "Wakad",
            "pincode": "411057",
        },
    )
    token_seller = s_res.json()["data"]["access_token"]

    b_res = client.post(
        "/auth/register",
        json={
            "name": "Order Buyer",
            "email": "obuyer@test.com",
            "phone": "9820011555",
            "password": "Password123!",
            "role": "reseller",
            "area": "Wakad",
            "pincode": "411057",
        },
    )
    token_buyer = b_res.json()["data"]["access_token"]

    # Listing
    l_res = client.post(
        "/listings",
        json={
            "category_id": str(cat.id),
            "title": "Aluminium Scrap",
            "quantity_kg": "30.000",
            "price_per_kg": "120.00",
            "is_negotiable": False,
            "area": "Wakad",
            "pincode": "411057",
        },
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    listing_id = l_res.json()["data"]["id"]

    # Offer
    o_res = client.post(
        f"/listings/{listing_id}/offers",
        json={"quantity_kg": "30.000", "price_per_kg": "120.00"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    offer_id = o_res.json()["data"]["id"]

    # Accept offer -> creates order
    acc_res = client.post(
        f"/offers/{offer_id}/accept",
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    order_id = acc_res.json()["data"]["order_id"]

    return token_seller, token_buyer, listing_id, order_id


def test_order_happy_path_and_weight_difference(client: TestClient, db_session: Session) -> None:
    token_seller, token_buyer, _, order_id = _setup_order(client, db_session)

    # Check order is initially confirmed
    get_res = client.get(f"/orders/{order_id}", headers={"Authorization": f"Bearer {token_buyer}"})
    assert get_res.status_code == 200
    order = get_res.json()["data"]
    assert order["status"] == "confirmed"

    # 1. Record collection weight
    w_col = client.post(
        f"/orders/{order_id}/weights",
        json={"stage": "collection", "weight_kg": "31.200"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    assert w_col.status_code == 201
    assert w_col.json()["data"]["stage"] == "collection"

    # Advance to collected
    t_col = client.post(
        f"/orders/{order_id}/transition",
        json={"target_status": "collected"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    assert t_col.status_code == 200
    assert t_col.json()["data"]["status"] == "collected"

    # 2. Record delivery weight
    w_del = client.post(
        f"/orders/{order_id}/weights",
        json={"stage": "delivery", "weight_kg": "30.500"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    assert w_del.status_code == 201

    # Advance to delivered
    t_del = client.post(
        f"/orders/{order_id}/transition",
        json={"target_status": "delivered"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    assert t_del.status_code == 200
    assert t_del.json()["data"]["status"] == "delivered"

    # Advance to completed
    t_comp = client.post(
        f"/orders/{order_id}/transition",
        json={"target_status": "completed"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    assert t_comp.status_code == 200
    final_order = t_comp.json()["data"]
    assert final_order["status"] == "completed"

    # Verify weight difference (31.200 - 30.500 = 0.700 kg loss)
    assert float(final_order["collection_weight_kg"]) == 31.2
    assert float(final_order["delivery_weight_kg"]) == 30.5
    assert round(float(final_order["weight_difference_kg"]), 3) == 0.700

    # Verify status history has 4 records (confirmed, collected, delivered, completed)
    assert len(final_order["status_history"]) == 4


def test_transition_validations_and_weight_enforcement(
    client: TestClient,
    db_session: Session,
) -> None:
    token_seller, token_buyer, _, order_id = _setup_order(client, db_session)

    # Seller attempts to move order forward -> 403 BUYER_ACTION_ONLY
    seller_attempt = client.post(
        f"/orders/{order_id}/transition",
        json={"target_status": "collected"},
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    assert seller_attempt.status_code == 403
    assert seller_attempt.json()["code"] == "BUYER_ACTION_ONLY"

    # Attempt to skip directly to delivered -> 400 INVALID_STATE_TRANSITION
    skip_attempt = client.post(
        f"/orders/{order_id}/transition",
        json={"target_status": "delivered"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    assert skip_attempt.status_code == 400
    assert skip_attempt.json()["code"] == "INVALID_STATE_TRANSITION"

    # Advance to collected WITHOUT collection weight -> 400 COLLECTION_WEIGHT_REQUIRED
    advance_no_weight = client.post(
        f"/orders/{order_id}/transition",
        json={"target_status": "collected"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    assert advance_no_weight.status_code == 400
    assert advance_no_weight.json()["code"] == "COLLECTION_WEIGHT_REQUIRED"

    # Record collection weight, advance to collected
    client.post(
        f"/orders/{order_id}/weights",
        json={"stage": "collection", "weight_kg": "30.000"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    client.post(
        f"/orders/{order_id}/transition",
        json={"target_status": "collected"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )

    # Advance to delivered WITHOUT delivery weight -> 400 DELIVERY_WEIGHT_REQUIRED
    advance_no_del_weight = client.post(
        f"/orders/{order_id}/transition",
        json={"target_status": "delivered"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    assert advance_no_del_weight.status_code == 400
    assert advance_no_del_weight.json()["code"] == "DELIVERY_WEIGHT_REQUIRED"

    # Cannot cancel once order has moved past confirmed
    cancel_attempt = client.post(
        f"/orders/{order_id}/transition",
        json={"target_status": "cancelled"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    assert cancel_attempt.status_code == 400
    assert cancel_attempt.json()["code"] == "INVALID_STATE_TRANSITION"


def test_order_cancellation_when_confirmed(client: TestClient, db_session: Session) -> None:
    _, token_buyer, _, order_id = _setup_order(client, db_session)

    # Buyer cancels while confirmed
    cancel_res = client.post(
        f"/orders/{order_id}/transition",
        json={"target_status": "cancelled"},
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["status"] == "cancelled"
