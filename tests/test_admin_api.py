import pytest
from fastapi.testclient import TestClient

from app.admin_api import create_app

KEY = "test-key"

GOOD = {
    "first_name": "Likhith",
    "last_name": "Edupuganti",
    "car_number": "TS09AB1234",
    "start": "2099-01-01 10:00",
    "end": "2099-01-01 12:00",
    "note": "Zone B has space",
}


@pytest.fixture
def app(tmp_path):
    return create_app(db_path=tmp_path / "admin.db", api_key=KEY)


@pytest.fixture
def client(app):
    return TestClient(app, headers={"X-API-Key": KEY})


def test_health_needs_no_key(app):
    assert TestClient(app).get("/health").status_code == 200


def test_missing_key_is_rejected(app):
    assert TestClient(app).get("/requests").status_code == 401


def test_wrong_key_is_rejected(app):
    response = TestClient(app, headers={"X-API-Key": "wrong"}).get("/requests")
    assert response.status_code == 401


def test_create_returns_a_pending_record(client):
    response = client.post("/requests", json=GOOD)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["car_number"] == "TS09AB1234"


def test_invalid_request_is_rejected_with_reasons(client):
    response = client.post("/requests", json={**GOOD, "car_number": "ABC"})
    assert response.status_code == 422
    assert "Car number" in str(response.json()["detail"])


def test_unknown_request_returns_404(client):
    assert client.get("/requests/RES-NOPE00").status_code == 404


def test_decision_updates_the_status(client):
    created = client.post("/requests", json=GOOD).json()
    pending = client.get("/requests", params={"status": "PENDING"}).json()
    assert len(pending) == 1

    response = client.post(
        f"/requests/{created['id']}/decision",
        json={"decision": "APPROVED", "reason": "ok"},
    )
    assert response.status_code == 200
    assert client.get(f"/requests/{created['id']}").json()["status"] == "APPROVED"
    assert client.get("/requests", params={"status": "PENDING"}).json() == []


def test_second_decision_conflicts(client):
    created = client.post("/requests", json=GOOD).json()
    url = f"/requests/{created['id']}/decision"
    client.post(url, json={"decision": "APPROVED"})
    assert client.post(url, json={"decision": "REFUSED"}).status_code == 409


def test_invalid_decision_value_is_rejected(client):
    created = client.post("/requests", json=GOOD).json()
    response = client.post(
        f"/requests/{created['id']}/decision", json={"decision": "MAYBE"}
    )
    assert response.status_code == 422


def test_service_refuses_to_start_without_a_key(monkeypatch, tmp_path):
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        create_app(db_path=tmp_path / "admin.db")