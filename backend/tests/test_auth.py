from fastapi.testclient import TestClient


def test_register_success(client: TestClient) -> None:
    payload = {
        "name": "Rohan Deshmukh",
        "email": "rohan.d@example.com",
        "phone": "9820099001",
        "password": "Password123!",
        "role": "individual",
        "area": "Wakad",
        "pincode": "411057",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["code"] == "SUCCESS"
    assert "access_token" in body["data"]
    assert body["data"]["user"]["email"] == "rohan.d@example.com"
    assert body["data"]["user"]["role"] == "individual"


def test_register_duplicate_email(client: TestClient) -> None:
    payload = {
        "name": "User One",
        "email": "dup@example.com",
        "phone": "9820099002",
        "password": "Password123!",
        "role": "reseller",
        "area": "Baner",
        "pincode": "411045",
    }
    res1 = client.post("/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/auth/register", json=payload)
    assert res2.status_code == 409
    body = res2.json()
    assert body["code"] == "EMAIL_ALREADY_EXISTS"


def test_login_success_and_me(client: TestClient) -> None:
    reg_payload = {
        "name": "Sneha Joshi",
        "email": "sneha.j@example.com",
        "phone": "9820099003",
        "password": "MySecretPassword1!",
        "role": "aggregator",
        "area": "Hadapsar",
        "pincode": "411028",
    }
    client.post("/auth/register", json=reg_payload)

    login_res = client.post(
        "/auth/login",
        json={"email": "sneha.j@example.com", "password": "MySecretPassword1!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["data"]["access_token"]
    assert token

    me_res = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()["data"]
    assert me_data["name"] == "Sneha Joshi"
    assert me_data["role"] == "aggregator"


def test_login_invalid_password(client: TestClient) -> None:
    reg_payload = {
        "name": "Ajay Kumar",
        "email": "ajay.k@example.com",
        "phone": "9820099004",
        "password": "CorrectPassword1!",
        "role": "individual",
        "area": "Kharadi",
        "pincode": "411014",
    }
    client.post("/auth/register", json=reg_payload)

    res = client.post(
        "/auth/login",
        json={"email": "ajay.k@example.com", "password": "WrongPassword!"},
    )
    assert res.status_code == 401
    assert res.json()["code"] == "INVALID_CREDENTIALS"


def test_get_me_unauthorized(client: TestClient) -> None:
    res = client.get("/me")
    assert res.status_code == 401
    assert res.json()["code"] == "UNAUTHORIZED"
