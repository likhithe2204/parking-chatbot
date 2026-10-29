import pytest
from fastapi.testclient import TestClient

from app.mcp_server import create_app

KEY = "test-key"

GOOD = {
    "first_name": "Likhith",
    "last_name": "Edupuganti",
    "car_number": "TS09AB1234",
    "start": "2026-12-05 10:00",
    "end": "2026-12-05 14:00",
    "approval_time": "2026-10-28T17:34:59",
}


@pytest.fixture
def reservations(tmp_path):
    return tmp_path / "reservations.txt"


@pytest.fixture
def client(reservations):
    app = create_app(path=reservations, api_key=KEY)
    # The MCP server only accepts localhost host names.
    with TestClient(app, base_url="http://127.0.0.1:8001") as test_client:
        yield test_client


def rpc(method, params=None, request_id=1):
    body = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        body["params"] = params
    return body


def post(client, body, key=KEY):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if key is not None:
        headers["X-API-Key"] = key
    return client.post("/mcp", headers=headers, json=body)


def save(client, **overrides):
    arguments = {**GOOD, **overrides}
    response = post(client, rpc("tools/call", {"name": "save_reservation", "arguments": arguments}))
    return response.json()["result"]


def text_of(result):
    return result["content"][0]["text"]


def test_health_needs_no_key(client):
    assert client.get("/health").status_code == 200


def test_missing_key_is_rejected(client):
    assert post(client, rpc("tools/list"), key=None).status_code == 401


def test_wrong_key_is_rejected(client):
    assert post(client, rpc("tools/list"), key="wrong").status_code == 401


def test_everything_except_health_needs_the_key(client):
    for path in ("/docs", "/openapi.json", "/anything"):
        assert client.get(path).status_code == 401


def test_rejected_call_writes_nothing(client, reservations):
    body = rpc("tools/call", {"name": "save_reservation", "arguments": GOOD})
    assert post(client, body, key="wrong").status_code == 401
    assert not reservations.exists()


def test_only_one_tool_is_exposed(client):
    tools = post(client, rpc("tools/list")).json()["result"]["tools"]
    assert [tool["name"] for tool in tools] == ["save_reservation"]


def test_valid_call_writes_the_reservation_line(client, reservations):
    result = save(client)
    assert result["isError"] is False
    assert text_of(result).startswith("SAVED: Likhith Edupuganti | TS09AB1234")
    assert reservations.read_text(encoding="utf-8").splitlines() == [
        "Likhith Edupuganti | TS09AB1234 | 2026-12-05 10:00 to 2026-12-05 14:00 "
        "| 2026-10-28 17:34:59"
    ]


def test_duplicate_call_is_reported_and_not_written_twice(client, reservations):
    save(client)
    result = save(client)
    assert text_of(result).startswith("ALREADY_RECORDED")
    assert len(reservations.read_text(encoding="utf-8").splitlines()) == 1


def test_invalid_reservation_is_rejected_and_not_written(client, reservations):
    result = save(client, car_number="ABC")
    assert result["isError"] is True
    assert "Car number" in text_of(result)
    assert not reservations.exists()


def test_server_refuses_to_start_without_a_key(monkeypatch, tmp_path):
    monkeypatch.delenv("MCP_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        create_app(path=tmp_path / "reservations.txt")