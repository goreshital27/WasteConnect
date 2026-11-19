from fastapi.testclient import TestClient


def test_frontend_served(client: TestClient) -> None:
    res = client.get("/")
    assert res.status_code == 200
    assert "WasteConnect" in res.text
    assert "Recyclable" in res.text


def test_static_js_served(client: TestClient) -> None:
    res = client.get("/static/app.js")
    assert res.status_code == 200
    assert "wasteconnect" in res.text.lower()
