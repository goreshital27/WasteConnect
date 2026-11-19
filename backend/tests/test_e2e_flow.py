from app.modules.catalog.models import WasteCategory
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_complete_demo_marketplace_lifecycle(client: TestClient, db_session: Session) -> None:
    """End-to-end user verification:

    1. Register demo reseller & household seller.
    2. Household seller creates an open recyclable listing.
    3. Reseller browses open listings, makes an offer.
    4. Household seller accepts offer (order confirmed, listing marked sold).
    5. Reseller records collection weight, transitions to collected.
    6. Reseller records delivery weight, transitions to delivered.
    7. Reseller marks order completed.
    8. Weight difference is calculated and verified.
    """
    # Create category
    cat = WasteCategory(code="pet_e2e", name="PET Plastic", unit="kg", is_active=True)
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)

    # 1. Register reseller and household seller
    client.post(
        "/auth/register",
        json={
            "name": "Sunil Scrap",
            "email": "sunil.e2e@example.com",
            "phone": "9820011001",
            "password": "Password123!",
            "role": "reseller",
            "area": "Wakad",
            "pincode": "411057",
        },
    )
    client.post(
        "/auth/register",
        json={
            "name": "Aarav Sharma",
            "email": "aarav.e2e@example.com",
            "phone": "9820011002",
            "password": "Password123!",
            "role": "individual",
            "area": "Wakad",
            "pincode": "411057",
        },
    )

    # Seller logs in
    s_login = client.post(
        "/auth/login",
        json={"email": "aarav.e2e@example.com", "password": "Password123!"},
    )
    token_seller = s_login.json()["data"]["access_token"]

    # 2. Seller creates listing
    l_create = client.post(
        "/listings",
        json={
            "category_id": str(cat.id),
            "title": "Clean Water Bottles Lot",
            "quantity_kg": "25.000",
            "price_per_kg": "24.00",
            "is_negotiable": True,
            "area": "Wakad",
            "pincode": "411057",
        },
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    listing_id = l_create.json()["data"]["id"]

    # 3. Reseller logs in & browses open listings
    b_login = client.post(
        "/auth/login",
        json={"email": "sunil.e2e@example.com", "password": "Password123!"},
    )
    token_reseller = b_login.json()["data"]["access_token"]

    browse_res = client.get("/listings", params={"status_filter": "open"})
    assert browse_res.status_code == 200

    # Reseller makes an offer
    offer_res = client.post(
        f"/listings/{listing_id}/offers",
        json={"quantity_kg": "25.000", "price_per_kg": "23.50"},
        headers={"Authorization": f"Bearer {token_reseller}"},
    )
    assert offer_res.status_code == 201
    offer_id = offer_res.json()["data"]["id"]

    # 4. Seller accepts the offer
    accept_res = client.post(
        f"/offers/{offer_id}/accept",
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    assert accept_res.status_code == 200
    order_id = accept_res.json()["data"]["order_id"]

    # Verify listing is now sold
    listing_check = client.get(f"/listings/{listing_id}")
    assert listing_check.json()["data"]["status"] == "sold"

    # 5. Buyer records collection weight & moves to collected
    client.post(
        f"/orders/{order_id}/weights",
        json={"stage": "collection", "weight_kg": "25.500"},
        headers={"Authorization": f"Bearer {token_reseller}"},
    )
    move_col = client.post(
        f"/orders/{order_id}/transition",
        json={"target_status": "collected"},
        headers={"Authorization": f"Bearer {token_reseller}"},
    )
    assert move_col.status_code == 200
    assert move_col.json()["data"]["status"] == "collected"

    # 6. Buyer records delivery weight & moves to delivered
    client.post(
        f"/orders/{order_id}/weights",
        json={"stage": "delivery", "weight_kg": "25.100"},
        headers={"Authorization": f"Bearer {token_reseller}"},
    )
    move_del = client.post(
        f"/orders/{order_id}/transition",
        json={"target_status": "delivered"},
        headers={"Authorization": f"Bearer {token_reseller}"},
    )
    assert move_del.status_code == 200
    assert move_del.json()["data"]["status"] == "delivered"

    # 7. Buyer completes order
    move_comp = client.post(
        f"/orders/{order_id}/transition",
        json={"target_status": "completed"},
        headers={"Authorization": f"Bearer {token_reseller}"},
    )
    assert move_comp.status_code == 200
    final_order = move_comp.json()["data"]
    assert final_order["status"] == "completed"

    # 8. Verify weight difference is 0.400 kg (25.500 - 25.100)
    assert round(float(final_order["weight_difference_kg"]), 3) == 0.400
    assert len(final_order["status_history"]) == 4
