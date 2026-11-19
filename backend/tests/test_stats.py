from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_stats_rate_card_and_impact(client: TestClient, db_session: Session) -> None:
    # Check rate card endpoint returns list
    rc_res = client.get("/stats/rate-card")
    assert rc_res.status_code == 200
    rc_body = rc_res.json()
    assert rc_body["code"] == "SUCCESS"
    assert isinstance(rc_body["data"], list)

    # Check impact endpoint returns total kg
    imp_res = client.get("/stats/impact")
    assert imp_res.status_code == 200
    imp_body = imp_res.json()
    assert imp_body["code"] == "SUCCESS"
    assert "total_diverted_kg" in imp_body["data"]
    assert "orders_diverted_count" in imp_body["data"]
