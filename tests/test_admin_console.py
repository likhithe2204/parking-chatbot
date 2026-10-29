from app import admin_console
from app.admin_client import AdminServiceError

PENDING = {
    "id": "RES-AAAAAA",
    "first_name": "Likhith",
    "last_name": "Edupuganti",
    "car_number": "TS09AB1234",
    "start": "2099-01-01 10:00",
    "end": "2099-01-01 12:00",
    "note": "Zone B has space",
    "status": "PENDING",
}


class FakeClient:
    def __init__(self, records):
        self.records = {r["id"]: dict(r) for r in records}
        self.decided = []

    def list_requests(self, status=None):
        return [r for r in self.records.values() if status is None or r["status"] == status]

    def get_request(self, request_id):
        return self.records[request_id]

    def decide(self, request_id, decision, reason=""):
        self.decided.append((request_id, decision, reason))
        self.records[request_id]["status"] = decision
        return self.records[request_id]


class BrokenClient:
    def list_requests(self, status=None):
        raise AdminServiceError("down")


def run_console(client, answers):
    outputs = []
    feed = iter(answers)
    admin_console.run(client, input_fn=lambda _="": next(feed), output_fn=outputs.append)
    return "\n".join(outputs)


def test_format_request_shows_the_details():
    text = admin_console.format_request(PENDING)
    assert "RES-AAAAAA" in text
    assert "TS09AB1234" in text
    assert "Zone B has space" in text


def test_administrator_can_approve():
    client = FakeClient([PENDING])
    output = run_console(client, ["RES-AAAAAA", "approve", "all good", "q"])
    assert client.decided == [("RES-AAAAAA", "APPROVED", "all good")]
    assert "marked APPROVED" in output


def test_administrator_can_refuse_with_a_reason():
    client = FakeClient([PENDING])
    run_console(client, ["RES-AAAAAA", "refuse", "zone full", "q"])
    assert client.decided == [("RES-AAAAAA", "REFUSED", "zone full")]


def test_skip_does_not_decide():
    client = FakeClient([PENDING])
    output = run_console(client, ["RES-AAAAAA", "skip", "q"])
    assert client.decided == []
    assert "Skipped" in output


def test_empty_queue_is_reported():
    output = run_console(FakeClient([]), ["q"])
    assert "No pending requests" in output


def test_service_error_stops_the_console():
    output = run_console(BrokenClient(), [])
    assert "Error: down" in output